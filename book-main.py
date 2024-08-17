from fastapi import FastAPI, HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./library.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class DBBook(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author_id = Column(Integer, ForeignKey("authors.id"))
    isbn = Column(String, unique=True, index=True)
    publication_year = Column(Integer)

class DBAuthor(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    birth_year = Column(Integer)

class DBBorrowRecord(Base):
    __tablename__ = "borrow_records"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    borrower_name = Column(String)
    borrow_date = Column(DateTime, default=datetime.utcnow)
    return_date = Column(DateTime, nullable=True)

Base.metadata.create_all(bind=engine)

# Pydantic models
class BookBase(BaseModel):
    title: str
    isbn: str
    publication_year: int

class BookCreate(BookBase):
    author_id: int

class Book(BookBase):
    id: int
    author_id: int

    class Config:
        orm_mode = True

class AuthorBase(BaseModel):
    name: str
    birth_year: int

class AuthorCreate(AuthorBase):
    pass

class Author(AuthorBase):
    id: int

    class Config:
        orm_mode = True

class BorrowRecordBase(BaseModel):
    book_id: int
    borrower_name: str

class BorrowRecordCreate(BorrowRecordBase):
    pass

class BorrowRecord(BorrowRecordBase):
    id: int
    borrow_date: datetime
    return_date: Optional[datetime] = None

    class Config:
        orm_mode = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

# Book routes
@app.post("/books/", response_model=Book)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    db_book = DBBook(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.get("/books/", response_model=List[Book])
def read_books(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    books = db.query(DBBook).offset(skip).limit(limit).all()
    return books

@app.get("/books/{book_id}", response_model=Book)
def read_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book: BookCreate, db: Session = Depends(get_db)):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in book.dict().items():
        setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.delete("/books/{book_id}", response_model=Book)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(db_book)
    db.commit()
    return db_book

# Author routes
@app.post("/authors/", response_model=Author)
def create_author(author: AuthorCreate, db: Session = Depends(get_db)):
    db_author = DBAuthor(**author.dict())
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author

@app.get("/authors/", response_model=List[Author])
def read_authors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    authors = db.query(DBAuthor).offset(skip).limit(limit).all()
    return authors

@app.get("/authors/{author_id}", response_model=Author)
def read_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(DBAuthor).filter(DBAuthor.id == author_id).first()
    if author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

# Borrow record routes
@app.post("/borrow/", response_model=BorrowRecord)
def create_borrow_record(borrow_record: BorrowRecordCreate, db: Session = Depends(get_db)):
    db_borrow_record = DBBorrowRecord(**borrow_record.dict())
    db.add(db_borrow_record)
    db.commit()
    db.refresh(db_borrow_record)
    return db_borrow_record

@app.get("/borrow/", response_model=List[BorrowRecord])
def read_borrow_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    borrow_records = db.query(DBBorrowRecord).offset(skip).limit(limit).all()
    return borrow_records

@app.put("/borrow/{record_id}/return", response_model=BorrowRecord)
def return_book(record_id: int, db: Session = Depends(get_db)):
    db_borrow_record = db.query(DBBorrowRecord).filter(DBBorrowRecord.id == record_id).first()
    if db_borrow_record is None:
        raise HTTPException(status_code=404, detail="Borrow record not found")
    if db_borrow_record.return_date is not None:
        raise HTTPException(status_code=400, detail="Book already returned")
    db_borrow_record.return_date = datetime.utcnow()
    db.commit()
    db.refresh(db_borrow_record)
    return db_borrow_record

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)