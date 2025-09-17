from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date as Date, timedelta


class UserBase(BaseModel):
    username: str
    login: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None


class UserLogin(BaseModel):
    login: str
    password: str


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None


class Category(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: Optional[int] = None
    created_at: datetime


class AccountBase(BaseModel):
    name: str
    balance: float


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    balance: Optional[float] = None


class Account(AccountBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime


class TransactionBase(BaseModel):
    title: str
    amount: float
    category_id: int
    account_id: int


class TransactionCreate(TransactionBase):
    done_at: Optional[datetime] = None


class TransactionUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    category_id: Optional[int] = None
    account_id: Optional[int] = None


class Transaction(TransactionBase):
    id: int
    done_at: datetime
    user: User
    category: Category
    account: Account


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None


class GoalBase(BaseModel):
    account_id: int
    target_amount: float
    deadline: Date


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    account_id: Optional[int] = None
    target_amount: Optional[float] = None
    deadline: Optional[Date] = None
    is_completed: Optional[bool] = None


class Goal(GoalBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    is_completed: bool
    created_at: datetime
    user: User
    account: Account


class ReminderBase(BaseModel):
    title: str
    amount: float
    date: Date
    recurrence: Optional[timedelta] = None


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[Date] = None
    recurrence: Optional[timedelta] = None
    is_active: Optional[bool] = None


class Reminder(ReminderBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    user: User
