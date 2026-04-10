create table if not exists components (
	id serial primary key,
	name varchar(100) not null unique,
	component_type varchar(50) not null,
	description text,
	created_at timestamp default current_timestamp
);
