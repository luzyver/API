from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()

supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role
)


def get_supabase() -> Client:
    """Dependency to get Supabase client"""
    return supabase
