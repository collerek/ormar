from typing import Optional

import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Keyword(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="keywords")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50)


class KeywordPrimaryModel(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="primary_models_keywords")

    id: int = ormar.Integer(primary_key=True)


class PrimaryModel(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="primary_models")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255, index=True)
    some_text: str = ormar.Text()
    some_other_text: Optional[str] = ormar.Text(nullable=True)
    keywords: Optional[list[Keyword]] = ormar.ManyToMany(
        Keyword, through=KeywordPrimaryModel
    )


class SecondaryModel(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="secondary_models")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    primary_model: PrimaryModel = ormar.ForeignKey(
        PrimaryModel, related_name="secondary_models"
    )


@pytest.mark.asyncio
async def test_create_primary_models():
    async with base_ormar_config.database:
        for name, some_text, some_other_text in [
            ("Primary 1", "Some text 1", "Some other text 1"),
            ("Primary 2", "Some text 2", "Some other text 2"),
            ("Primary 3", "Some text 3", "Some other text 3"),
            ("Primary 4", "Some text 4", "Some other text 4"),
            ("Primary 5", "Some text 5", "Some other text 5"),
            ("Primary 6", "Some text 6", "Some other text 6"),
            ("Primary 7", "Some text 7", "Some other text 7"),
            ("Primary 8", "Some text 8", "Some other text 8"),
            ("Primary 9", "Some text 9", "Some other text 9"),
            ("Primary 10", "Some text 10", "Some other text 10"),
        ]:
            await PrimaryModel(
                name=name, some_text=some_text, some_other_text=some_other_text
            ).save()

        for tag_id in [1, 2, 3, 4, 5]:
            await Keyword.objects.create(name=f"Tag {tag_id}")

        p1 = await PrimaryModel.objects.get(pk=1)
        p2 = await PrimaryModel.objects.get(pk=2)
        for i in range(1, 6):
            keyword = await Keyword.objects.get(pk=i)
            if i % 2 == 0:
                await p1.keywords.add(keyword)
            else:
                await p2.keywords.add(keyword)
        models = await PrimaryModel.objects.select_related("keywords").limit(5).all()

        assert len(models) == 5
        assert len(models[0].keywords) == 2
        assert len(models[1].keywords) == 3
        assert len(models[2].keywords) == 0

        models2 = (
            await PrimaryModel.objects.select_related("keywords")
            .limit(5)
            .offset(3)
            .all()
        )
        assert len(models2) == 5
        assert [x.name for x in models2] != [x.name for x in models]
        assert [x.name for x in models2] == [
            "Primary 4",
            "Primary 5",
            "Primary 6",
            "Primary 7",
            "Primary 8",
        ]

        models3 = (
            await PrimaryModel.objects.select_related("keywords")
            .limit(5, limit_raw_sql=True)
            .all()
        )

        assert len(models3) == 2
        assert len(models3[0].keywords) == 2
        assert len(models3[1].keywords) == 3

        models4 = (
            await PrimaryModel.objects.offset(1)
            .select_related("keywords")
            .limit(5, limit_raw_sql=True)
            .all()
        )

        assert len(models4) == 3
        assert [x.name for x in models4] == ["Primary 1", "Primary 2", "Primary 3"]
        assert len(models4[0].keywords) == 1
        assert len(models4[1].keywords) == 3
        assert len(models4[2].keywords) == 0

        models5 = (
            await PrimaryModel.objects.select_related("keywords")
            .offset(2, limit_raw_sql=True)
            .limit(5)
            .all()
        )

        assert len(models5) == 3
        assert [x.name for x in models5] == ["Primary 2", "Primary 3", "Primary 4"]
        assert len(models5[0].keywords) == 3
        assert len(models5[1].keywords) == 0
        assert len(models5[2].keywords) == 0


create_test_database = init_tests(base_ormar_config)
