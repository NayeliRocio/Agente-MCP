-- Ejecutar UNA VEZ en Supabase > SQL Editor. No borra datos.
create schema if not exists agentlab;
revoke all on schema agentlab from public, anon, authenticated;
create table if not exists agentlab.products (
 id text primary key,
 name text not null,
 stock integer not null check(stock >= 0)
);
create table if not exists agentlab.conversations (
 id uuid primary key,
 user_id uuid not null,
 created_at timestamptz not null default now()
);
create index if not exists conversations_owner on agentlab.conversations(user_id);
create table if not exists agentlab.messages (
 id bigint generated always as identity primary key,
 conversation_id uuid not null references agentlab.conversations(id),
 role text not null check(role in ('user','assistant','system')),
 content text not null,
 created_at timestamptz not null default now()
);
create table if not exists agentlab.confirmations (
 id uuid primary key,
 conversation_id uuid not null references agentlab.conversations(id),
 user_id uuid not null,
 product_id text not null references agentlab.products(id),
 quantity integer not null check(quantity between 1 and 100),
 status text not null default 'pending' check(status in ('pending','approved','cancelled','used')),
 expires_at timestamptz not null default now() + interval '10 minutes'
);
create table if not exists agentlab.reservations (
 id uuid primary key,
 user_id uuid not null,
 product_id text not null references agentlab.products(id),
 quantity integer not null check(quantity > 0),
 confirmation_id uuid not null unique references agentlab.confirmations(id),
 created_at timestamptz not null default now()
);
create table if not exists agentlab.tool_executions (
 id bigint generated always as identity primary key,
 conversation_id uuid not null references agentlab.conversations(id),
 tool_name text not null,
 status text not null,
 duration_ms integer not null,
 result jsonb not null,
 created_at timestamptz not null default now()
);
-- Defensa adicional: backend por conexión PostgreSQL. Sin acceso directo desde Data API.
alter table agentlab.products enable row level security;
alter table agentlab.conversations enable row level security;
alter table agentlab.messages enable row level security;
alter table agentlab.confirmations enable row level security;
alter table agentlab.reservations enable row level security;
alter table agentlab.tool_executions enable row level security;
revoke all on all tables in schema agentlab from public, anon, authenticated;
insert into agentlab.products(id,name,stock) values
 ('TEC-01','Teclado USB',12), ('MOU-01','Mouse óptico',8), ('CAM-01','Cámara web',3)
on conflict(id) do nothing;
