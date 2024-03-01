-- generate table of articles
create table articles(
    article_id serial primary key, 
    article_title VARCHAR(200) not null,
    article_htmlcontent TEXT,
    article_deltacontent TEXT,
    image_file BYTEA,
    header_image BOOLEAN default FALSE,
    published BOOLEAN default FALSE,
    user_id INT not null,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    generation_time TIMESTAMP not null default CURRENT_TIMESTAMP, 
    last_edit TIMESTAMP not null default CURRENT_TIMESTAMP
);


-- generate table of users, each user has associated username, id
create table users(
    user_id serial primary key, -- this will probably be the session ID
    userName text, 
    email text
)

-- sample insert new article
insert into articles(article_title, article_content) values('giraffe', 'fake content')
insert into userSavedArticles(article_title, article_content) values('giraffe', 'fake content')

-- sample edit article
-- TODO: MAKE SURE TITLE CAN"T BE CHANGED ON ARTICLE EDIT PAGE, ONLY ON ARTICLE GEN
-- OTHERWISE, WILL NEED A DELETE TO MAKE SURE PREVIOUS ARTICLE TITLE ENTRY NOT IN DB
-- ALSO THE UPDATE DEPENDS ON ARTICLE TITLE
update articles set article_content="new content" where article_title="article_name"


-- THESE ARE THE SQL COMMAND FOR SEARCH 

CREATE INDEX articleContent ON articles USING GIN (to_tsvector('english', article_content));
CREATE INDEX articleTitle ON articles USING GIN (to_tsvector('english', article_title));

select * from articles where to_tsvector('english', article_content) @@ plainto_tsquery('english', 'found') or 
to_tsvector('english', article_title) @@ plainto_tsquery('english', 'found') 
order by ts_rank(to_tsvector('english', article_content), 'found');