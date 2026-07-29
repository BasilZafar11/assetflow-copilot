import asyncio
from app.db.database import init_db, AsyncSessionLocal, TenantMapping, UserMapping
from app.core.config import settings
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

async def seed():
    print("Initializing SQLite Database...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Tenant Mapping
        tenant_workspace_id = "T0BGEMDKKT9"
        print(f"Upserting Tenant Mapping for workspace {tenant_workspace_id}...")
        tenant_stmt = sqlite_insert(TenantMapping).values(
            slack_workspace_id=tenant_workspace_id,
            assetflow_org_id=1,
            admin_token=settings.assetflow_admin_token,
            approvals_channel_id="C0BGY0TSC5P",
        ).on_conflict_do_update(
            index_elements=['slack_workspace_id'],
            set_={
                'assetflow_org_id': 1,
                'admin_token': settings.assetflow_admin_token,
                'approvals_channel_id': "C0BGY0TSC5P",
            }
        )
        await session.execute(tenant_stmt)

        # 2. User Mappings (Slack User ID -> AssetFlow User ID)
        # Note: We support mapping to workspace "T0BGEMDKKT9" and "T01" to be safe.
        users_to_seed = [
            # Original demo users
            {"slack_user_id": "U0BGWCC5JH0", "slack_workspace_id": "T01", "assetflow_user_id": 7, "email": "devyashrasela@gmail.com"},
            {"slack_user_id": "U0BGW2TB23C", "slack_workspace_id": "T01", "assetflow_user_id": 9, "email": "padhimayank@gmail.com"},
            {"slack_user_id": "U0BGY2SV77U", "slack_workspace_id": "T01", "assetflow_user_id": 10, "email": "basilzafar2424@gmail.com"},
            
            # Workspace specific duplicate mappings or updates
            {"slack_user_id": "U0BGWCC5JH0_t0b", "slack_user_id_real": "U0BGWCC5JH0", "slack_workspace_id": "T0BGEMDKKT9", "assetflow_user_id": 7, "email": "devyashrasela@gmail.com"},
            {"slack_user_id": "U0BGW2TB23C_t0b", "slack_user_id_real": "U0BGW2TB23C", "slack_workspace_id": "T0BGEMDKKT9", "assetflow_user_id": 9, "email": "padhimayank@gmail.com"},
            {"slack_user_id": "U0BGY2SV77U_t0b", "slack_user_id_real": "U0BGY2SV77U", "slack_workspace_id": "T0BGEMDKKT9", "assetflow_user_id": 10, "email": "basilzafar2424@gmail.com"},

            # Testing accounts (Slack Hack and Devpost)
            {"slack_user_id": "U0BH4J44NJ0", "slack_workspace_id": "T0BGEMDKKT9", "assetflow_user_id": 12, "email": "slackhack@salesforce.com"},
            {"slack_user_id": "U0BGYSCPWCE", "slack_workspace_id": "T0BGEMDKKT9", "assetflow_user_id": 11, "email": "testing@devpost.com"},
        ]

        print("Upserting User Mappings...")
        for u in users_to_seed:
            slack_id = u.get("slack_user_id_real", u["slack_user_id"])
            user_stmt = sqlite_insert(UserMapping).values(
                slack_user_id=slack_id,
                slack_workspace_id=u["slack_workspace_id"],
                assetflow_user_id=u["assetflow_user_id"],
                email=u["email"]
            ).on_conflict_do_update(
                index_elements=['slack_user_id'],
                set_={
                    'slack_workspace_id': u["slack_workspace_id"],
                    'assetflow_user_id': u["assetflow_user_id"],
                    'email': u["email"]
                }
            )
            await session.execute(user_stmt)

        try:
            await session.commit()
            print("SQLite Seeding finished successfully.")
        except Exception as e:
            await session.rollback()
            print(f"Error committing seed data: {e}")

if __name__ == "__main__":
    asyncio.run(seed())
