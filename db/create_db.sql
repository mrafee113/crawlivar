create table locations
(
    id           serial primary key,
    name         text,
    name_english text,
    href         text
);

create table phones
(
    id          serial primary key,
    number      text,
    location_id integer references locations (id)
);

create table categories
(
    id           serial primary key,
    name         text,
    name_english text
);

create table articles
(
    id               serial primary key,
    title            text,
    date_published   date,
    time_published   time,
    phone_id         integer references phones (id),
    category_id      integer references categories (id),
    location_id      integer references locations (id),
    location_href    text,
    area_size        numeric,
    price            numeric,
    publisher_type   text,
    description      text,
    uri              text,
    datetime_crawled timestamp,
    datetime_added   timestamp default now(),
    datetime_updated timestamp
);

create or replace function update_datetime_updated_column() returns trigger
as
$$
begin
    new.datetime_updated = now();
    return new;
end;
$$;

create trigger articles_datetime_updated_update_trigger
    after update
    on articles
    for each row
execute procedure update_datetime_updated_column();