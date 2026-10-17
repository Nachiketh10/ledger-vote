"""
Custom `flask` CLI commands. Registered in app/__init__.py via app.cli.

Usage:
    flask create-super-admin --name "Jane Doe" --email jane@example.com --password "Str0ng!Passw0rd"
    flask revoke-voter-sessions --email votetest_xxxxxx@example.com
"""

import click
from flask import Flask
from flask.cli import with_appcontext

from app.extensions import db
from app.models.admin import Admin
from app.models.voter import Voter
from app.services.auth_service import hash_password
from app.services import voter_admin_service
from app.models.enums import ActorType


def register_cli(app: Flask) -> None:
    @app.cli.command("create-super-admin")
    @click.option("--name", required=True, help="Full name of the Super Admin.")
    @click.option("--email", required=True, help="Login email.")
    @click.option(
        "--password",
        required=True,
        help="Login password (must meet the standard strength rules).",
    )
    @with_appcontext
    def create_super_admin(name: str, email: str, password: str):
        """Create the first (or an additional) Super Admin account."""
        email = email.lower().strip()

        if Admin.query.filter_by(email=email).first():
            click.echo(click.style(f"An admin with email '{email}' already exists.", fg="red"))
            return

        from app.security.validators import validate_password_strength

        is_valid, msg = validate_password_strength(password)
        if not is_valid:
            click.echo(click.style(f"Password rejected: {msg}", fg="red"))
            return

        admin = Admin(name=name, email=email, password_hash=hash_password(password))
        db.session.add(admin)
        db.session.commit()

        click.echo(click.style(f"Super Admin created: {email}", fg="green"))
        click.echo("You can now log in via POST /api/auth/login with role=\"super_admin\".")

    @app.cli.command("revoke-voter-sessions")
    @click.option("--email", required=True, help="Email of the voter whose sessions to revoke.")
    @with_appcontext
    def revoke_voter_sessions(email: str):
        """
        Force-logs-out a voter from every active session — quick fix for
        the 'multiple sessions' / 'multiple devices' fraud flags that
        build up from repeated test logins during development, without
        needing to create a brand-new voter each time. In production,
        prefer the admin API endpoint (POST /api/admin/voters/<id>/revoke-sessions)
        so the action gets attributed to a specific admin in the audit log.
        """
        email = email.lower().strip()
        voter = Voter.query.filter_by(email=email).first()
        if not voter:
            click.echo(click.style(f"No voter found with email '{email}'.", fg="red"))
            return

        count = voter_admin_service.revoke_all_sessions(voter, ActorType.SYSTEM, None)
        click.echo(click.style(f"Revoked {count} active session(s) for {email}.", fg="green"))

    @app.cli.command("reset-voter-biometrics")
    @click.option("--email", required=True, help="Email of the voter whose face data to clear.")
    @with_appcontext
    def reset_voter_biometrics(email: str):
        """
        Deletes a voter's stored face embedding and clears
        has_face_registered, so they can register a fresh face from
        scratch. Does NOT touch vote history or sessions — pair with
        revoke-voter-sessions if you also need a clean slate on sessions.
        """
        email = email.lower().strip()
        voter = Voter.query.filter_by(email=email).first()
        if not voter:
            click.echo(click.style(f"No voter found with email '{email}'.", fg="red"))
            return

        removed = voter_admin_service.reset_biometrics(voter, ActorType.SYSTEM, None)
        parts = []
        if removed["face"]:
            parts.append("face embedding")
        if parts:
            click.echo(click.style(f"Removed: {', '.join(parts)} for {email}.", fg="green"))
        else:
            click.echo(click.style(f"No biometric data was registered for {email} — nothing to remove.", fg="yellow"))

    @app.cli.command("reset-voter-test-data")
    @click.option("--email", required=True, help="Email of the voter to fully reset for re-testing.")
    @with_appcontext
    def reset_voter_test_data(email: str):
        """
        Convenience command for iterative testing: revokes all sessions
        AND clears face enrollment for a voter in one go, so you can
        re-run the full register->verify->vote flow against the SAME
        test voter repeatedly instead of creating a new one every
        time. Does NOT touch vote history — if the voter already voted
        in an election, they still can't vote again in that same one
        (by design); use a different/new election to test another vote.
        """
        email = email.lower().strip()
        voter = Voter.query.filter_by(email=email).first()
        if not voter:
            click.echo(click.style(f"No voter found with email '{email}'.", fg="red"))
            return

        session_count = voter_admin_service.revoke_all_sessions(voter, ActorType.SYSTEM, None)
        removed = voter_admin_service.reset_biometrics(voter, ActorType.SYSTEM, None)

        click.echo(click.style(f"Revoked {session_count} session(s) for {email}.", fg="green"))
        parts = [k for k, v in removed.items() if v]
        if parts:
            click.echo(click.style(f"Removed biometric data: {', '.join(parts)}.", fg="green"))
        else:
            click.echo(click.style("No biometric data was registered — nothing to remove there.", fg="yellow"))
        click.echo(click.style(f"{email} is ready for a fresh test pass.", fg="green"))

    @app.cli.command("seed-demo-data")
    @with_appcontext
    def seed_demo_data():
        """
        Creates a small, idempotent set of demo data so a reviewer can
        see the app populated without manual setup: one Election Admin
        account and one sample election with three candidates (left in
        'draft' status — start it manually if you want to demo voting).

        Does NOT create demo voters: a voter needs a real face
        registered through the actual browser flow to be useful for
        anything (voting requires real biometric capture), so a fake
        seeded voter would just be misleading clutter. Use the actual
        Register page, or scripts/setup_vote_test_election.py for a
        fully scripted test election + voter.
        """
        from datetime import datetime, timedelta, timezone
        from app.models.admin import ElectionAdmin
        from app.models.election import Election
        from app.models.candidate import Candidate
        from app.models.enums import ElectionStatus

        created_anything = False

        election_admin = ElectionAdmin.query.filter_by(email="admin2@example.com").first()
        if not election_admin:
            election_admin = ElectionAdmin(
                name="Demo Election Admin",
                email="admin2@example.com",
                password_hash=hash_password("Demo@Admin123!"),
            )
            db.session.add(election_admin)
            db.session.commit()
            click.echo(click.style(
                "Created Election Admin: admin2@example.com / Demo@Admin123!", fg="green"
            ))
            created_anything = True
        else:
            click.echo("Election Admin admin2@example.com already exists — skipping.")

        existing_election = Election.query.filter_by(title="Student Council Election (Demo)").first()
        if not existing_election:
            now = datetime.now(timezone.utc)
            election = Election(
                title="Student Council Election (Demo)",
                description="A sample election seeded for demonstration purposes.",
                start_date=now,
                end_date=now + timedelta(days=7),
                status=ElectionStatus.DRAFT,
                created_by_id=election_admin.id,
            )
            db.session.add(election)
            db.session.flush()

            for name, party in [
                ("Alex Rivera", "Independent"),
                ("Jordan Chen", "Student Progress Party"),
                ("Sam Okafor", "Campus Unity"),
            ]:
                db.session.add(Candidate(election_id=election.id, name=name, party=party))

            db.session.commit()
            click.echo(click.style(
                f"Created demo election '{election.title}' with 3 candidates (status: draft).", fg="green"
            ))
            created_anything = True
        else:
            click.echo("Demo election already exists — skipping.")

        if not created_anything:
            click.echo(click.style("Nothing to do — demo data already present.", fg="yellow"))
        else:
            click.echo(click.style(
                "\nTo demo voting: register a voter through the app (with a real face "
                "registered), have this Election Admin verify + mark them eligible, "
                "then start the election.", fg="cyan"
            ))

    @app.cli.command("wipe-test-data")
    @click.option(
        "--yes", is_flag=True, default=False,
        help="Skip the confirmation prompt (use in scripts, not by hand).",
    )
    @with_appcontext
    def wipe_test_data(yes: bool):
        """
        Deletes ALL voters, elections, candidates, votes, blockchain
        blocks, fraud logs, and audit logs — a full reset for repeated
        end-to-end testing. Deliberately KEEPS the admins and
        election_admins tables untouched, so your Super Admin login
        still works afterward without needing `create-super-admin` again.

        This is a destructive, irreversible operation — only use it in
        a development/test database, never against real election data.
        """
        from sqlalchemy import text

        if not yes:
            click.echo(click.style(
                "This will PERMANENTLY delete all voters, elections, candidates, "
                "votes, blockchain blocks, fraud logs, and audit logs.\n"
                "Admin accounts (Super Admin / Election Admin logins) will be kept.",
                fg="yellow",
            ))
            if not click.confirm("Are you sure you want to continue?"):
                click.echo("Cancelled.")
                return

        # voters/elections cascade to everything that references them
        # (candidates, votes, blockchain, fraud_logs, sessions,
        # face_embeddings, and the eligibility/assignment join tables).
        # audit_logs has no FK to voters/elections (actor_id is a plain
        # UUID column), so it's listed explicitly rather than relying
        # on CASCADE to reach it.
        db.session.execute(text("TRUNCATE TABLE voters, elections, audit_logs CASCADE"))
        db.session.commit()

        click.echo(click.style(
            "All voter, election, vote, blockchain, fraud, and audit data has been wiped. "
            "Admin accounts were preserved.",
            fg="green",
        ))
