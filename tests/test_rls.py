from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID

import psycopg
import pytest
from django.contrib.auth import get_user_model
from django.db import DatabaseError, connections, transaction

from agentledger.tenancy.context import (
    activate_tenant,
    identity_transaction,
    tenant_transaction,
)
from apps.catalog.models import Product, Vendor
from apps.inventory.models import InventoryItem
from apps.organizations.models import Organization, OrganizationMember

pytestmark = [
    pytest.mark.rls,
    pytest.mark.skipif(
        os.getenv("AGENTLEDGER_RLS_TESTS") != "1",
        reason="run through scripts/verify_rls.py",
    ),
    pytest.mark.django_db(
        transaction=True,
        databases={"default", "owner_runtime", "app_runtime", "worker_runtime"},
    ),
]


@dataclass(frozen=True)
class IsolationFixture:
    user_a_id: UUID
    user_b_id: UUID
    organization_a_id: UUID
    organization_b_id: UUID
    item_a_id: UUID
    item_b_id: UUID


@pytest.fixture
def isolation_fixture():
    user_model = get_user_model()
    user_a = user_model.objects.create_user("rls-a@example.com")
    user_b = user_model.objects.create_user("rls-b@example.com")
    organization_a = Organization.objects.create(name="RLS Firm A")
    organization_b = Organization.objects.create(name="RLS Firm B")
    OrganizationMember.objects.create(
        user=user_a,
        organization=organization_a,
        role=OrganizationMember.Role.OWNER,
    )
    OrganizationMember.objects.create(
        user=user_b,
        organization=organization_b,
        role=OrganizationMember.Role.OWNER,
    )
    item_a = InventoryItem.objects.create(
        organization=organization_a,
        display_name="Inventory A",
        vendor_name="Vendor A",
    )
    item_b = InventoryItem.objects.create(
        organization=organization_b,
        display_name="Inventory B",
        vendor_name="Vendor B",
    )
    fixture = IsolationFixture(
        user_a.id,
        user_b.id,
        organization_a.id,
        organization_b.id,
        item_a.id,
        item_b.id,
    )
    yield fixture
    InventoryItem.objects.all().delete()
    OrganizationMember.objects.all().delete()
    Organization.objects.all().delete()
    user_model.objects.all().delete()


def assert_insufficient_privilege(captured) -> None:
    assert isinstance(captured.value, DatabaseError)
    assert isinstance(captured.value.__cause__, psycopg.errors.InsufficientPrivilege)


def current_user(using: str) -> str:
    with connections[using].cursor() as cursor:
        cursor.execute("SELECT current_user")
        return cursor.fetchone()[0]


def raw_inventory_ids(using: str) -> set[UUID]:
    with connections[using].cursor() as cursor:
        cursor.execute("SELECT id FROM inventory_items")
        return {row[0] for row in cursor.fetchall()}


@pytest.mark.parametrize(
    ("using", "expected"),
    [
        ("owner_runtime", "agentledger_owner"),
        ("app_runtime", "agentledger_app"),
        ("worker_runtime", "agentledger_worker"),
    ],
)
def test_restricted_alias_uses_the_expected_database_identity(using, expected):
    assert current_user(using) == expected


def test_app_runtime_can_read_global_catalog_without_write_authority():
    vendor = Vendor.objects.create(name="RLS Catalog Vendor")
    Product.objects.create(vendor=vendor, name="RLS Catalog Product", category="Test")

    assert Product.objects.using("app_runtime").count() == 1
    with pytest.raises(DatabaseError) as captured:
        with transaction.atomic(using="app_runtime"):
            Vendor.objects.using("app_runtime").create(name="Forbidden Catalog Write")

    assert_insufficient_privilege(captured)


def test_database_roles_have_the_required_privilege_boundary():
    with connections["app_runtime"].cursor() as cursor:
        cursor.execute(
            """
            SELECT rolname, rolsuper, rolbypassrls, rolinherit, rolcanlogin
            FROM pg_roles
            WHERE rolname IN (
                'agentledger_owner', 'agentledger_app', 'agentledger_worker'
            )
            ORDER BY rolname
            """
        )
        assert cursor.fetchall() == [
            ("agentledger_app", False, False, False, True),
            ("agentledger_owner", False, False, False, True),
            ("agentledger_worker", False, False, False, True),
        ]
        cursor.execute(
            """
            SELECT pg_get_userbyid(relowner)
            FROM pg_class
            WHERE oid = 'inventory_items'::regclass
            """
        )
        assert cursor.fetchone()[0] == "agentledger_owner"


def test_organization_scoped_tables_have_required_column_and_forced_rls():
    with connections["app_runtime"].cursor() as cursor:
        cursor.execute(
            """
            SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity, a.attnotnull
            FROM pg_class AS c
            JOIN pg_attribute AS a ON a.attrelid = c.oid
            JOIN pg_namespace AS n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relkind = 'r'
              AND a.attname = 'organization_id'
            ORDER BY c.relname
            """
        )
        assert cursor.fetchall() == [
            ("inventory_items", True, True, True),
            ("organizations_organizationmember", True, True, True),
        ]
        cursor.execute(
            """
            SELECT cmd, roles, qual IS NOT NULL, with_check IS NOT NULL
            FROM pg_policies
            WHERE schemaname = 'public'
              AND tablename = 'inventory_items'
              AND policyname = 'inventory_items_tenant_policy'
            """
        )
        assert cursor.fetchone() == (
            "ALL",
            ["agentledger_app", "agentledger_worker"],
            True,
            True,
        )


def test_identity_bootstrap_exposes_only_the_users_own_membership(
    isolation_fixture,
):
    fixture = isolation_fixture
    with identity_transaction(fixture.user_a_id, using="app_runtime"):
        membership_organizations = set(
            OrganizationMember.objects.using("app_runtime").values_list(
                "organization_id", flat=True
            )
        )
        organization_ids = set(
            Organization.objects.using("app_runtime").values_list("id", flat=True)
        )

    assert membership_organizations == {fixture.organization_a_id}
    assert organization_ids == {fixture.organization_a_id}


def test_app_role_unfiltered_orm_and_raw_sql_are_tenant_isolated(
    isolation_fixture,
):
    fixture = isolation_fixture
    with tenant_transaction(fixture.organization_a_id, using="app_runtime"):
        orm_ids = set(
            InventoryItem.objects.using("app_runtime").values_list("id", flat=True)
        )
        sql_ids = raw_inventory_ids("app_runtime")

    assert orm_ids == {fixture.item_a_id}
    assert sql_ids == {fixture.item_a_id}


def test_direct_cross_tenant_primary_key_lookup_is_inaccessible(isolation_fixture):
    fixture = isolation_fixture
    with tenant_transaction(fixture.organization_a_id, using="app_runtime"):
        exists = (
            InventoryItem.objects.using("app_runtime")
            .filter(pk=fixture.item_b_id)
            .exists()
        )

    assert exists is False


def test_cross_tenant_insert_is_rejected(isolation_fixture):
    fixture = isolation_fixture
    with pytest.raises(DatabaseError) as captured:
        with tenant_transaction(fixture.organization_a_id, using="app_runtime"):
            InventoryItem.objects.using("app_runtime").create(
                organization_id=fixture.organization_b_id,
                display_name="Forbidden insert",
                vendor_name="Forbidden vendor",
            )

    assert_insufficient_privilege(captured)


def test_cross_tenant_update_affects_no_rows(isolation_fixture):
    fixture = isolation_fixture
    with tenant_transaction(fixture.organization_a_id, using="app_runtime"):
        updated = (
            InventoryItem.objects.using("app_runtime")
            .filter(pk=fixture.item_b_id)
            .update(display_name="Forbidden update")
        )

    assert updated == 0
    assert InventoryItem.objects.get(pk=fixture.item_b_id).display_name == "Inventory B"


def test_missing_tenant_context_fails_closed(isolation_fixture):
    with pytest.raises(DatabaseError) as captured:
        with transaction.atomic(using="app_runtime"):
            raw_inventory_ids("app_runtime")

    assert_insufficient_privilege(captured)


def test_context_on_default_connection_does_not_unlock_app_runtime(
    isolation_fixture,
):
    fixture = isolation_fixture
    with transaction.atomic(using="default"):
        activate_tenant(fixture.organization_a_id, using="default")
        with pytest.raises(DatabaseError) as captured:
            with transaction.atomic(using="app_runtime"):
                raw_inventory_ids("app_runtime")

    assert_insufficient_privilege(captured)


def test_worker_role_cannot_read_another_tenants_business_rows(isolation_fixture):
    fixture = isolation_fixture
    with tenant_transaction(fixture.organization_a_id, using="worker_runtime"):
        assert current_user("worker_runtime") == "agentledger_worker"
        assert raw_inventory_ids("worker_runtime") == {fixture.item_a_id}
