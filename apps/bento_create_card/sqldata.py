import pymysql
import time
import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, String, Column, Integer, DateTime, MetaData, Table, Text
from sqlalchemy.orm import sessionmaker
from apps.bento_create_card.main_transactionrecord import TransactionRecord
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")


engine = create_engine("mysql+pymysql://wuanlin:trybest_1@rm-j6c3t1i83rgylsuamvo.mysql.rds.aliyuncs.com:3306/bento")
Base = declarative_base()

class BentoCard(Base):
    __tablename__ = "bento_create_card"
    id = Column(Integer, primary_key=True)
    alias = Column(String(30), unique=True)
    card_id = Column(String(30), nullable=True)
    card_number = Column(String(30), nullable=True)
    card_amount = Column(String(30), nullable=True)
    card_cvv = Column(String(30), nullable=True)
    card_validity = Column(String(30), nullable=True)
    create_time = Column(DateTime)
    label = Column(String(30), nullable=True)
    attribution = Column(String(30), nullable=True)

    def __repr__(self):
        return "<card >{}:{}".format(self.alias, self.card_number)

class BentoUser(Base):
    __tablename__ = "bento_card_name"
    id = Column(Integer, primary_key=True)
    username = Column(String(25), unique=True)
    state = Column(String(20), nullable=True)
    label = Column(String(25), nullable=True)

    def __repr__(self):
        return "<card >{}".format(self.username)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

if __name__ == "__main__":
    d = TransactionRecord().alias()
    data = []
    s = session.query(BentoCard).filter(BentoCard.label=="gt测试").all()
    for i in s:
        for n in d:
            if i.alias == n.get("alias"):
                print(n.get("availableAmount"))

