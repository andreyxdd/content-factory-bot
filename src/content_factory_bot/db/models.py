from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PrimaryLanguage(StrEnum):
    EN = "en"
    RU = "ru"


class ProviderKind(StrEnum):
    TELEGRAM = "telegram"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"


class Creator(Base):
    """Allowlisted Creator preferences (1:1 with telegram user id)."""

    __tablename__ = "creators"

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    primary_language: Mapped[str] = mapped_column(String(8), default=PrimaryLanguage.EN)
    review_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    research_default_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class PersonalityProfile(Base):
    __tablename__ = "personality_profiles"

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ready: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_version: Mapped[int] = mapped_column(Integer, default=1)
    style_card_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    values_block_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    tribal_block_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ProfileAnswer(Base):
    __tablename__ = "profile_answers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    question_key: Mapped[str] = mapped_column(String(64))
    answer_text: Mapped[str] = mapped_column(Text)
    option_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class AllowlistEntry(Base):
    """Telegram user id permitted to use the bot."""

    __tablename__ = "allowlist_entries"

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    added_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ContentSession(Base):
    __tablename__ = "content_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    title: Mapped[str] = mapped_column(String(255), default="Untitled")
    state: Mapped[str] = mapped_column(String(32), default="setup")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    web_research: Mapped[bool] = mapped_column(Boolean, default=True)
    cover_generation: Mapped[bool] = mapped_column(Boolean, default=False)
    destinations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_draft_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_storage_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class SessionInput(Base):
    __tablename__ = "session_inputs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, index=True)
    input_type: Mapped[str] = mapped_column(String(16), default="text")
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class DraftRound(Base):
    __tablename__ = "draft_rounds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, index=True)
    round_no: Mapped[int] = mapped_column(Integer)
    options_json: Mapped[str] = mapped_column(Text)
    selected_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_refinement: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class PublishedArtifact(Base):
    __tablename__ = "published_artifacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, index=True)
    provider: Mapped[str] = mapped_column(String(32))
    external_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ProviderConnection(Base):
    """OAuth or Telegram channel linkage for one Creator × provider."""

    __tablename__ = "provider_connections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    provider: Mapped[str] = mapped_column(String(32))  # ProviderKind value
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending | active | error
    external_account_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    credentials_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class SupportedLocale(Base):
    __tablename__ = "supported_locales"
    __table_args__ = (
        Index(
            "uq_supported_locales_single_default",
            "is_default",
            unique=True,
            postgresql_where=text("is_default = true"),
            sqlite_where=text("is_default = 1"),
        ),
    )

    code: Mapped[str] = mapped_column(String(16), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ProfileArtifactSet(Base):
    __tablename__ = "profile_artifact_sets"
    __table_args__ = (
        UniqueConstraint(
            "telegram_user_id",
            "locale",
            "profile_version",
            name="uq_profile_artifact_set_version",
        ),
        Index(
            "uq_profile_artifact_sets_active_locale",
            "telegram_user_id",
            "locale",
            unique=True,
            postgresql_where=text("is_active = true"),
            sqlite_where=text("is_active = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    locale: Mapped[str] = mapped_column(
        String(16), ForeignKey("supported_locales.code"), index=True
    )
    profile_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="active")  # pending|active|failed
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_locale: Mapped[str | None] = mapped_column(
        String(16), ForeignKey("supported_locales.code"), nullable=True
    )
    style_card_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    values_block_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    tribal_block_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class TranslationConsentRecord(Base):
    __tablename__ = "translation_consent_records"
    __table_args__ = (
        UniqueConstraint(
            "telegram_user_id",
            "source_locale",
            "target_locale",
            "policy_version",
            "approved",
            name="uq_translation_consent_scope",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    source_locale: Mapped[str] = mapped_column(
        String(16), ForeignKey("supported_locales.code")
    )
    target_locale: Mapped[str] = mapped_column(
        String(16), ForeignKey("supported_locales.code")
    )
    policy_version: Mapped[int] = mapped_column(Integer, default=1)
    action_id: Mapped[str] = mapped_column(String(64))
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
