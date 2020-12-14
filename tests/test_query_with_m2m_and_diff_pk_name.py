import asyncio
from datetime import date
from typing import List, Optional, Union

import databases
import pytest
import sqlalchemy

import ormar

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class MainMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Role(ormar.Model):
    class Meta(MainMeta):
        pass

    name: str = ormar.Text(primary_key=True)
    order: int = ormar.Integer(default=0)
    description: str = ormar.Text()


class Company(ormar.Model):
    class Meta(MainMeta):
        pass

    name: str = ormar.Text(primary_key=True)


class UserRoleCompany(ormar.Model):
    class Meta(MainMeta):
        pass


class User(ormar.Model):
    class Meta(MainMeta):
        pass

    registrationnumber: str = ormar.Text(primary_key=True)
    company: Company = ormar.ForeignKey(Company)
    name: str = ormar.Text()
    role: Optional[Role] = ormar.ForeignKey(Role)
    roleforcompanies: Optional[Union[Company, List[Company]]] = ormar.ManyToMany(Company, through=UserRoleCompany)
    lastupdate: date = ormar.DateTime(server_default=sqlalchemy.func.now())


@pytest.mark.asyncio
async def test_create_primary_models():
    async with database:
        print("adding role")
        role_0 = await Role.objects.create(name="user", order=0, description="no administration right")
        role_1 = await Role.objects.create(name="admin", order=1, description="standard administration right")
        role_2 = await Role.objects.create(name="super_admin", order=2, description="super administration right")
        assert await Role.objects.count() == 3

        print("adding company")
        company_0 = await Company.objects.create(name="Company")
        company_1 = await Company.objects.create(name="Subsidiary Company 1")
        company_2 = await Company.objects.create(name="Subsidiary Company 2")
        company_3 = await Company.objects.create(name="Subsidiary Company 3")
        assert await Company.objects.count() == 4

        print("adding user")
        user = await User.objects.create(registrationnumber="00-00000", company=company_0, name="admin", role=role_1)
        assert await User.objects.count() == 1

        print("removing user")
        await user.delete()
        assert await User.objects.count() == 0

        print("adding user with company-role")
        companies: List[Company] = [company_1, company_2]
        # user = await User.objects.create(registrationnumber="00-00000", company=company_0, name="admin", role=role_1, roleforcompanies=companies)
        user = await User.objects.create(registrationnumber="00-00000", company=company_0, name="admin", role=role_1)
        # print(User.__fields__)
        await user.roleforcompanies.add(company_1)
        await user.roleforcompanies.add(company_2)

        users = await User.objects.select_related("roleforcompanies").all()
        # print(jsonpickle.encode(jsonable_encoder(users), unpicklable=False, keys=True))

    """

    This is the request generated:
    'SELECT
    users.registrationnumber as registrationnumber,
    users.company as company,
    users.name as name, users.role as role,
    users.lastupdate as lastupdate,
    cy24b4_userrolecompanys.id as cy24b4_id,
    cy24b4_userrolecompanys.company as cy24b4_company,
    cy24b4_userrolecompanys.user as cy24b4_user,
    jn50a4_companys.name as jn50a4_name \n
    FROM users
    LEFT OUTER JOIN userrolecompanys cy24b4_userrolecompanys ON cy24b4_userrolecompanys.user=users.id
    LEFT OUTER JOIN companys jn50a4_companys ON jn50a4_companys.name=cy24b4_userrolecompanys.company
    ORDER BY users.registrationnumber, jn50a4_companys.name'

    There is an error in the First LEFT OUTER JOIN generated:
    ... companys.user=users.id
    should be:
   ... companys.user=users.registrationnumber

    There is also a \n in the midle of the string...

    The execution produce the error: column users.id does not exist
    """
