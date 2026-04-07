"""
Seed script: inserts sample Uzbek sport data into PostgreSQL.
Run: python scripts/seed_data.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.athlete import Athlete
from app.models.coach import Coach
from app.models.competition import Competition
from app.models.result import Result
from app.models.user import User, UserRole

engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def seed():
    async with Session() as db:
        # ── Users ─────────────────────────────────────────────
        admin = User(
            username="admin",
            email="admin@sport.uz",
            hashed_password=hash_password("Admin@123"),
            role=UserRole.ADMIN,
        )
        user1 = User(
            username="user1",
            email="user1@sport.uz",
            hashed_password=hash_password("User@123"),
            role=UserRole.USER,
        )
        db.add_all([admin, user1])
        await db.flush()

        # ── Coaches ───────────────────────────────────────────
        coaches_data = [
            Coach(full_name="Bahodir Toshmatov", region="Toshkent shahri", sport_type="Boks", experience_years=15),
            Coach(full_name="Sarvar Yusupov", region="Samarqand viloyati", sport_type="Kurash", experience_years=20),
            Coach(full_name="Dilnoza Karimova", region="Farg'ona viloyati", sport_type="Gimnastika", experience_years=12),
            Coach(full_name="Jasur Mirzayev", region="Andijon viloyati", sport_type="Judo", experience_years=18),
            Coach(full_name="Mansur Holiqov", region="Namangan viloyati", sport_type="Futbol", experience_years=10),
        ]
        db.add_all(coaches_data)
        await db.flush()

        c_boks, c_kurash, c_gimn, c_judo, c_futbol = coaches_data

        # ── Athletes ──────────────────────────────────────────
        athletes_data = [
            # Boks
            Athlete(full_name="Sardor Rahimov", birth_date=date(1998, 3, 15),
                    region="Toshkent shahri", sport_type="Boks", rank="Xalqaro master", coach_id=c_boks.id),
            Athlete(full_name="Jahongir Qodirov", birth_date=date(2000, 7, 22),
                    region="Toshkent viloyati", sport_type="Boks", rank="Sport ustasi", coach_id=c_boks.id),
            Athlete(full_name="Bobur Abdullayev", birth_date=date(2002, 1, 10),
                    region="Sirdaryo viloyati", sport_type="Boks", rank="1-daraja", coach_id=c_boks.id),
            Athlete(full_name="Sherzod Normatov", birth_date=date(1999, 5, 18),
                    region="Toshkent shahri", sport_type="Boks", rank="Sport ustasi", coach_id=c_boks.id),
            # Kurash
            Athlete(full_name="Akbar Yunusov", birth_date=date(1997, 11, 3),
                    region="Samarqand viloyati", sport_type="Kurash", rank="Xalqaro master", coach_id=c_kurash.id),
            Athlete(full_name="Murod Tursunov", birth_date=date(2001, 8, 14),
                    region="Buxoro viloyati", sport_type="Kurash", rank="Sport ustasi", coach_id=c_kurash.id),
            Athlete(full_name="Farrux Xasanov", birth_date=date(2003, 4, 27),
                    region="Samarqand viloyati", sport_type="Kurash", rank="1-daraja", coach_id=c_kurash.id),
            Athlete(full_name="Otabek Ismoilov", birth_date=date(1996, 12, 9),
                    region="Qashqadaryo viloyati", sport_type="Kurash", rank="Xalqaro master", coach_id=c_kurash.id),
            # Gimnastika
            Athlete(full_name="Nilufar Ergasheva", birth_date=date(2004, 2, 20),
                    region="Farg'ona viloyati", sport_type="Gimnastika", rank="Sport ustasi", coach_id=c_gimn.id),
            Athlete(full_name="Zulfiya Nazarova", birth_date=date(2005, 6, 11),
                    region="Farg'ona viloyati", sport_type="Gimnastika", rank="1-daraja", coach_id=c_gimn.id),
            Athlete(full_name="Malika Sobirova", birth_date=date(2003, 9, 5),
                    region="Toshkent shahri", sport_type="Gimnastika", rank="Sport ustasi", coach_id=c_gimn.id),
            Athlete(full_name="Sevinch Qosimova", birth_date=date(2006, 1, 30),
                    region="Andijon viloyati", sport_type="Gimnastika", rank="2-daraja", coach_id=c_gimn.id),
            # Judo
            Athlete(full_name="Eldor Hasanov", birth_date=date(1995, 10, 8),
                    region="Andijon viloyati", sport_type="Judo", rank="Xalqaro master", coach_id=c_judo.id),
            Athlete(full_name="Ulugbek Razzaqov", birth_date=date(1999, 3, 25),
                    region="Namangan viloyati", sport_type="Judo", rank="Sport ustasi", coach_id=c_judo.id),
            Athlete(full_name="Bekzod Tojiboyev", birth_date=date(2000, 7, 16),
                    region="Andijon viloyati", sport_type="Judo", rank="1-daraja", coach_id=c_judo.id),
            Athlete(full_name="Sanjar Fattoyev", birth_date=date(2002, 11, 2),
                    region="Farg'ona viloyati", sport_type="Judo", rank="Sport ustasi", coach_id=c_judo.id),
            # Futbol
            Athlete(full_name="Husayn Normatov", birth_date=date(1998, 4, 12),
                    region="Namangan viloyati", sport_type="Futbol", rank=None, coach_id=c_futbol.id),
            Athlete(full_name="Ibrohim Salimov", birth_date=date(2000, 8, 22),
                    region="Farg'ona viloyati", sport_type="Futbol", rank=None, coach_id=c_futbol.id),
            Athlete(full_name="Davron Eshmatov", birth_date=date(2001, 2, 7),
                    region="Toshkent shahri", sport_type="Futbol", rank=None, coach_id=c_futbol.id),
            Athlete(full_name="Alisher Mirzayev", birth_date=date(1997, 6, 19),
                    region="Namangan viloyati", sport_type="Futbol", rank=None, coach_id=c_futbol.id),
        ]
        db.add_all(athletes_data)
        await db.flush()

        # ── Competitions ──────────────────────────────────────
        comps_data = [
            Competition(name="O'zbekiston Chempionati 2023", date=date(2023, 3, 20),
                        location="Toshkent", sport_type="Boks"),
            Competition(name="Osiyo Chempionati 2023", date=date(2023, 6, 15),
                        location="Toshkent", sport_type="Boks"),
            Competition(name="O'zbekiston Chempionati 2023", date=date(2023, 4, 10),
                        location="Samarqand", sport_type="Kurash"),
            Competition(name="Jahon Chempionati 2023", date=date(2023, 10, 5),
                        location="Toshkent", sport_type="Kurash"),
            Competition(name="O'zbekiston Chempionati 2023", date=date(2023, 5, 8),
                        location="Farg'ona", sport_type="Gimnastika"),
            Competition(name="Osiyo Kubogi 2022", date=date(2022, 9, 12),
                        location="Toshkent", sport_type="Judo"),
            Competition(name="O'zbekiston Chempionati 2022", date=date(2022, 4, 18),
                        location="Andijon", sport_type="Judo"),
            Competition(name="Markaziy Osiyo Chempionati 2023", date=date(2023, 7, 22),
                        location="Toshkent", sport_type="Futbol"),
        ]
        db.add_all(comps_data)
        await db.flush()

        comp_boks1, comp_boks2, comp_kurash1, comp_kurash2, \
            comp_gimn, comp_judo2, comp_judo1, comp_futbol = comps_data

        a = {ath.full_name: ath for ath in athletes_data}

        # ── Results ───────────────────────────────────────────
        results_data = [
            # Boks O'zbekiston 2023
            Result(athlete_id=a["Sardor Rahimov"].id, competition_id=comp_boks1.id, place=1, score=None, year=2023),
            Result(athlete_id=a["Jahongir Qodirov"].id, competition_id=comp_boks1.id, place=2, score=None, year=2023),
            Result(athlete_id=a["Sherzod Normatov"].id, competition_id=comp_boks1.id, place=3, score=None, year=2023),
            # Boks Osiyo 2023
            Result(athlete_id=a["Sardor Rahimov"].id, competition_id=comp_boks2.id, place=2, score=None, year=2023),
            Result(athlete_id=a["Jahongir Qodirov"].id, competition_id=comp_boks2.id, place=4, score=None, year=2023),
            # Kurash O'zbekiston 2023
            Result(athlete_id=a["Akbar Yunusov"].id, competition_id=comp_kurash1.id, place=1, score=None, year=2023),
            Result(athlete_id=a["Otabek Ismoilov"].id, competition_id=comp_kurash1.id, place=2, score=None, year=2023),
            Result(athlete_id=a["Murod Tursunov"].id, competition_id=comp_kurash1.id, place=3, score=None, year=2023),
            # Kurash Jahon 2023
            Result(athlete_id=a["Akbar Yunusov"].id, competition_id=comp_kurash2.id, place=3, score=None, year=2023),
            # Gimnastika 2023
            Result(athlete_id=a["Nilufar Ergasheva"].id, competition_id=comp_gimn.id, place=1, score=9.7, year=2023),
            Result(athlete_id=a["Zulfiya Nazarova"].id, competition_id=comp_gimn.id, place=2, score=9.4, year=2023),
            Result(athlete_id=a["Malika Sobirova"].id, competition_id=comp_gimn.id, place=3, score=9.1, year=2023),
            # Judo O'zbekiston 2022
            Result(athlete_id=a["Eldor Hasanov"].id, competition_id=comp_judo1.id, place=1, score=None, year=2022),
            Result(athlete_id=a["Ulugbek Razzaqov"].id, competition_id=comp_judo1.id, place=2, score=None, year=2022),
            # Judo Osiyo 2022
            Result(athlete_id=a["Eldor Hasanov"].id, competition_id=comp_judo2.id, place=2, score=None, year=2022),
            Result(athlete_id=a["Bekzod Tojiboyev"].id, competition_id=comp_judo2.id, place=5, score=None, year=2022),
            # Futbol 2023
            Result(athlete_id=a["Husayn Normatov"].id, competition_id=comp_futbol.id, place=None, score=None, year=2023),
            Result(athlete_id=a["Ibrohim Salimov"].id, competition_id=comp_futbol.id, place=None, score=None, year=2023),
        ]
        db.add_all(results_data)
        await db.commit()

    print(f"✅ Seed tugadi:")
    print(f"   Foydalanuvchilar: admin (Admin@123), user1 (User@123)")
    print(f"   Trenerlar: {len(coaches_data)}")
    print(f"   Sportchilar: {len(athletes_data)}")
    print(f"   Musobaqalar: {len(comps_data)}")
    print(f"   Natijalar: {len(results_data)}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
