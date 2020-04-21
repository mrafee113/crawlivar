BEGIN;
--
-- Create model Location
--
CREATE TABLE "isfahan_locations"
(
    "id"           serial NOT NULL PRIMARY KEY,
    "name"         text   NOT NULL,
    "name_english" text   NOT NULL,
    "href"         text   NOT NULL
);
--
-- Create model Phone
--
CREATE TABLE "isfahan_phones"
(
    "id"          serial  NOT NULL PRIMARY KEY,
    "number"      text    NOT NULL UNIQUE,
    "location_id" integer NOT NULL
);
--
-- Create model Category
--
CREATE TABLE "isfahan_categories"
(
    "id"           serial NOT NULL PRIMARY KEY,
    "name"         text   NOT NULL,
    "name_english" text   NOT NULL
);
--
-- Create model Article
--
CREATE TABLE "isfahan_articles"
(
    "id"               serial                   NOT NULL PRIMARY KEY,
    "title"            text                     NOT NULL,
    "date_published"   date                     NOT NULL,
    "time_published"   time                     NULL,
    "location_href"    text                     NOT NULL,
    "area_size"        numeric(14, 2)           NULL,
    "price"            numeric(18, 2)           NULL,
    "publisher_type"   text                     NOT NULL,
    "description"      text                     NOT NULL,
    "uri"              text                     NOT NULL,
    "datetime_crawled" timestamp with time zone NULL,
    "datetime_added"   timestamp with time zone NOT NULL,
    "datetime_updated" timestamp with time zone NOT NULL,
    "category_id"      integer                  NOT NULL,
    "location_id"      integer                  NOT NULL,
    "phone_id"         integer                  NOT NULL
);
ALTER TABLE "isfahan_locations"
    ADD CONSTRAINT "isfahan_locations_name_name_english_d299320a_uniq" UNIQUE ("name", "name_english");
ALTER TABLE "isfahan_phones"
    ADD CONSTRAINT "isfahan_phones_location_id_813792ab_fk_isfahan_locations_id" FOREIGN KEY ("location_id") REFERENCES "isfahan_locations" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "isfahan_phones_number_994170a3_like" ON "isfahan_phones" ("number" text_pattern_ops);
CREATE INDEX "isfahan_phones_location_id_813792ab" ON "isfahan_phones" ("location_id");
ALTER TABLE "isfahan_categories"
    ADD CONSTRAINT "isfahan_categories_name_name_english_9596d92d_uniq" UNIQUE ("name", "name_english");
ALTER TABLE "isfahan_articles"
    ADD CONSTRAINT "isfahan_articles_category_id_97eb11cd_fk_isfahan_categories_id" FOREIGN KEY ("category_id") REFERENCES "isfahan_categories" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "isfahan_articles"
    ADD CONSTRAINT "isfahan_articles_location_id_33aec416_fk_isfahan_locations_id" FOREIGN KEY ("location_id") REFERENCES "isfahan_locations" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "isfahan_articles"
    ADD CONSTRAINT "isfahan_articles_phone_id_de0cce32_fk_isfahan_phones_id" FOREIGN KEY ("phone_id") REFERENCES "isfahan_phones" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "isfahan_articles_category_id_97eb11cd" ON "isfahan_articles" ("category_id");
CREATE INDEX "isfahan_articles_location_id_33aec416" ON "isfahan_articles" ("location_id");
CREATE INDEX "isfahan_articles_phone_id_de0cce32" ON "isfahan_articles" ("phone_id");
COMMIT;
