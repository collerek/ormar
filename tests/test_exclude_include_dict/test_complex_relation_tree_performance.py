from datetime import datetime
from typing import List, Optional, Union

import databases
import ormar as orm
import pydantic
import pytest
import sqlalchemy

from tests.settings import create_config
from tests.lifespan import init_tests

base_ormar_config = create_config()


class ChagenlogRelease(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)

    ormar_config = base_ormar_config.copy(tablename="changelog_release")


class CommitIssue(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)

    ormar_config = base_ormar_config.copy(tablename="commit_issues")


class CommitLabel(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)

    ormar_config = base_ormar_config.copy(tablename="commit_label")


class MergeRequestCommit(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)

    ormar_config = base_ormar_config.copy(tablename="merge_request_commits")


class MergeRequestIssue(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)

    ormar_config = base_ormar_config.copy(tablename="merge_request_issues")


class MergeRequestLabel(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)

    ormar_config = base_ormar_config.copy(tablename="merge_request_labels")


class ProjectLabel(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)

    ormar_config = base_ormar_config.copy(tablename="project_label")


class PushCommit(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)

    ormar_config = base_ormar_config.copy(tablename="push_commit")


class PushLabel(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)

    ormar_config = base_ormar_config.copy(tablename="push_label")


class TagCommit(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)

    ormar_config = base_ormar_config.copy(tablename="tag_commits")


class TagIssue(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)

    ormar_config = base_ormar_config.copy(tablename="tag_issue")


class TagLabel(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)

    ormar_config = base_ormar_config.copy(tablename="tag_label")


class UserProject(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)
    access_level: int = orm.Integer(default=0)

    ormar_config = base_ormar_config.copy(tablename="user_project")


class Label(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)
    title: str = orm.String(max_length=100)
    description: str = orm.Text(default="")
    type: str = orm.String(max_length=100, default="")

    ormar_config = base_ormar_config.copy(tablename="labels")


class Project(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)
    name: str = orm.String(max_length=100)
    description: str = orm.Text(default="")
    git_url: str = orm.String(max_length=500, default="")
    labels: Optional[Union[List[Label], Label]] = orm.ManyToMany(
        Label, through=ProjectLabel, ondelete="CASCADE", onupdate="CASCADE"
    )
    changelog_jira_tag: str = orm.String(max_length=100, default="")
    change_type_jira_tag: str = orm.String(max_length=100, default="")
    jira_prefix: str = orm.String(max_length=10, default="SAN")
    type: str = orm.String(max_length=10, default="cs")
    target_branch_name: str = orm.String(max_length=100, default="master")
    header: str = orm.String(max_length=250, default="")
    jira_url: str = orm.String(max_length=500)
    changelog_file: str = orm.String(max_length=250, default="")
    version_file: str = orm.String(max_length=250, default="")

    ormar_config = base_ormar_config.copy(tablename="projects")


class Issue(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)
    summary: str = orm.Text(default="")
    description: str = orm.Text(default="")
    changelog: str = orm.Text(default="")
    link: str = orm.String(max_length=500)
    issue_type: str = orm.String(max_length=100)
    key: str = orm.String(max_length=100)
    change_type: str = orm.String(max_length=100, default="")
    data: pydantic.Json = orm.JSON(default={})

    ormar_config = base_ormar_config.copy(tablename="issues")


class User(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)
    username: str = orm.String(max_length=100, unique=True)
    name: str = orm.String(max_length=200, default="")

    ormar_config = base_ormar_config.copy(tablename="users")


class Branch(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)
    name: str = orm.String(max_length=200)
    description: str = orm.Text(default="")
    automatic_tags: bool = orm.Boolean(default=False)
    is_it_locked: bool = orm.Boolean(default=True)
    prefix_tag: str = orm.String(max_length=50, default="")
    postfix_tag: str = orm.String(max_length=50, default="")
    project: Project = orm.ForeignKey(Project, ondelete="CASCADE", onupdate="CASCADE")

    ormar_config = base_ormar_config.copy(tablename="branches")


class Changelog(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)
    content: str = orm.Text(default="")
    version: str = orm.Text(default="")
    past_changelog: int = orm.Integer(default=0)
    label: Label = orm.ForeignKey(
        Label, nullable=True, ondelete="CASCADE", onupdate="CASCADE"
    )
    project: Project = orm.ForeignKey(Project, ondelete="CASCADE", onupdate="CASCADE")
    created_date: datetime = orm.DateTime(default=datetime.utcnow())

    ormar_config = base_ormar_config.copy(tablename="changelogs")


class Commit(orm.Model):
    id: str = orm.String(max_length=500, primary_key=True)
    short_id: str = orm.String(max_length=500)
    title: str = orm.String(max_length=500)
    message: str = orm.Text(default="")
    url = orm.String(max_length=500, default="")
    author_name = orm.String(max_length=500, default="")
    labels: Optional[Union[List[Label], Label]] = orm.ManyToMany(
        Label, through=CommitLabel, ondelete="CASCADE", onupdate="CASCADE"
    )
    issues: Optional[Union[List[Issue], Issue]] = orm.ManyToMany(
        Issue, through=CommitIssue, ondelete="CASCADE", onupdate="CASCADE"
    )

    ormar_config = base_ormar_config.copy(tablename="commits")


class MergeRequest(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)
    idd: int = orm.Integer(default=0)
    title: str = orm.String(max_length=500)
    state: str = orm.String(max_length=100)
    merge_status: str = orm.String(max_length=100)
    description: str = orm.Text(default="")
    source: Branch = orm.ForeignKey(Branch, related_name="source")
    target: Branch = orm.ForeignKey(Branch, related_name="target")
    labels: Optional[Union[List[Label], Label]] = orm.ManyToMany(
        Label, through=MergeRequestLabel, ondelete="CASCADE", onupdate="CASCADE"
    )
    commits: Optional[Union[List[Commit], Commit]] = orm.ManyToMany(
        Commit, through=MergeRequestCommit, ondelete="CASCADE", onupdate="CASCADE"
    )
    issues: Optional[Union[List[Issue], Issue]] = orm.ManyToMany(
        Issue, through=MergeRequestIssue, ondelete="CASCADE", onupdate="CASCADE"
    )
    project: Project = orm.ForeignKey(Project, ondelete="CASCADE", onupdate="CASCADE")

    ormar_config = base_ormar_config.copy(tablename="merge_requests")


class Push(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)
    branch: Branch = orm.ForeignKey(
        Branch, nullable=True, ondelete="CASCADE", onupdate="CASCADE"
    )
    has_locking_changes: bool = orm.Boolean(default=False)
    sha: str = orm.String(max_length=200)
    labels: Optional[Union[List[Label], Label]] = orm.ManyToMany(
        Label, through=PushLabel, ondelete="CASCADE", onupdate="CASCADE"
    )
    commits: Optional[Union[List[Commit], Commit]] = orm.ManyToMany(
        Commit,
        through=PushCommit,
        through_relation_name="push",
        through_reverse_relation_name="commit_id",
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
    author: User = orm.ForeignKey(User, ondelete="CASCADE", onupdate="CASCADE")
    project: Project = orm.ForeignKey(Project, ondelete="CASCADE", onupdate="CASCADE")

    ormar_config = base_ormar_config.copy(tablename="pushes")


class Tag(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)
    name: str = orm.String(max_length=200)
    ref: str = orm.String(max_length=200)
    project: Project = orm.ForeignKey(Project, ondelete="CASCADE", onupdate="CASCADE")
    title: str = orm.String(max_length=200, default="")
    description: str = orm.Text(default="")
    commits: Optional[Union[List[Commit], Commit]] = orm.ManyToMany(
        Commit,
        through=TagCommit,
        through_relation_name="tag",
        through_reverse_relation_name="commit_id",
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
    issues: Optional[Union[List[Issue], Issue]] = orm.ManyToMany(
        Issue, through=TagIssue, ondelete="CASCADE", onupdate="CASCADE"
    )
    labels: Optional[Union[List[Label], Label]] = orm.ManyToMany(
        Label, through=TagLabel, ondelete="CASCADE", onupdate="CASCADE"
    )
    user: User = orm.ForeignKey(
        User, nullable=True, ondelete="CASCADE", onupdate="CASCADE"
    )
    branch: Branch = orm.ForeignKey(
        Branch, nullable=True, ondelete="CASCADE", onupdate="CASCADE"
    )

    ormar_config = base_ormar_config.copy(tablename="tags")


class Release(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)
    title: str = orm.String(max_length=200, default="")
    description: str = orm.Text(default="")
    tag: Tag = orm.ForeignKey(Tag, ondelete="CASCADE", onupdate="CASCADE")
    changelogs: List[Changelog] = orm.ManyToMany(
        Changelog, through=ChagenlogRelease, ondelete="CASCADE", onupdate="CASCADE"
    )
    data: pydantic.Json = orm.JSON(default={})

    ormar_config = base_ormar_config.copy(tablename="releases")


class Webhook(orm.Model):
    id: int = orm.Integer(name="id", primary_key=True)
    object_kind = orm.String(max_length=100)
    project: Project = orm.ForeignKey(Project, ondelete="CASCADE", onupdate="CASCADE")
    merge_request: MergeRequest = orm.ForeignKey(
        MergeRequest, nullable=True, ondelete="CASCADE", onupdate="CASCADE"
    )
    tag: Tag = orm.ForeignKey(
        Tag, nullable=True, ondelete="CASCADE", onupdate="CASCADE"
    )
    push: Push = orm.ForeignKey(
        Push, nullable=True, ondelete="CASCADE", onupdate="CASCADE"
    )
    created_at: datetime = orm.DateTime(default=datetime.now())
    data: pydantic.Json = orm.JSON(default={})
    status: int = orm.Integer(default=200)
    error: str = orm.Text(default="")


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_very_complex_relation_map():
    async with base_ormar_config.database:
        tags = [
            {"id": 18, "name": "name-18", "ref": "ref-18"},
            {"id": 17, "name": "name-17", "ref": "ref-17"},
            {"id": 12, "name": "name-12", "ref": "ref-12"},
        ]
        payload = [
            {
                "id": 9,
                "title": "prueba-2321",
                "description": "\n<!--- start changelog ver.v.1.3.0.0 -->"
                "Description 1"
                "<!--- end changelog ver.v.1.3.0.0 -->\n",
                "data": {},
            },
            {
                "id": 8,
                "title": "prueba-123-prod",
                "description": "\n<!--- start changelog ver.v.1.3.0.0 -->"
                "Description 2"
                "<!--- end changelog ver.v.1.3.0.0 -->\n",
                "data": {},
            },
            {
                "id": 6,
                "title": "prueba-3-2",
                "description": "\n<!--- start changelog ver.v.1.3.0.0 -->"
                "Description 3"
                "<!--- end changelog ver.v.1.3.0.0 -->\n",
                "data": {},
            },
        ]
        saved_tags = []
        for tag in tags:
            saved_tags.append(await Tag(**tag).save())

        for ind, pay in enumerate(payload):
            await Release(**pay, tag=saved_tags[ind]).save()

        releases = await Release.objects.order_by(Release.id.desc()).all()
        dicts = [release.model_dump() for release in releases]

        result = [
            {
                "id": 9,
                "title": "prueba-2321",
                "description": "\n<!--- start changelog ver.v.1.3.0.0 -->"
                "Description 1"
                "<!--- end changelog ver.v.1.3.0.0 -->\n",
                "data": {},
                "tag": {
                    "id": 18,
                },
                "changelogs": [],
            },
            {
                "id": 8,
                "title": "prueba-123-prod",
                "description": "\n<!--- start changelog ver.v.1.3.0.0 -->"
                "Description 2"
                "<!--- end changelog ver.v.1.3.0.0 -->\n",
                "data": {},
                "tag": {
                    "id": 17,
                },
                "changelogs": [],
            },
            {
                "id": 6,
                "title": "prueba-3-2",
                "description": "\n<!--- start changelog ver.v.1.3.0.0 -->"
                "Description 3"
                "<!--- end changelog ver.v.1.3.0.0 -->\n",
                "data": {},
                "tag": {
                    "id": 12,
                },
                "changelogs": [],
            },
        ]

        assert dicts == result
