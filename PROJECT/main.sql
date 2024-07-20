create table user_account(
id varchar(20),
foreign key(id) references users(id),
balance int,
account int
);

create table users(
id varchar(20) primary key,
password varchar(20),
chknum char(4)
);

create table detail(
id varchar(10),
foreign key(id) references users(id),
pay_date date,
pay int
);
