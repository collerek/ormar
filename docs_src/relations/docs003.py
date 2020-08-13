import databases
import sqlalchemy
import orm

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class SchoolClass(orm.Model):
    __tablename__ = "schoolclasses"
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)


class Category(orm.Model):
    __tablename__ = "categories"
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)


class Student(orm.Model):
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)
    schoolclass = orm.ForeignKey(SchoolClass)
    category = orm.ForeignKey(Category)


class Teacher(orm.Model):
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)
    schoolclass = orm.ForeignKey(SchoolClass)
    category = orm.ForeignKey(Category)
