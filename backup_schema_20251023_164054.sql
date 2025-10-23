--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Homebrew)
-- Dumped by pg_dump version 14.18 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO crm_user;

--
-- Name: employees; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.employees (
    id uuid NOT NULL,
    first_name character varying(255) NOT NULL,
    last_name character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    is_deleted boolean NOT NULL,
    deleted_at timestamp without time zone,
    created_by_id uuid,
    updated_by_id uuid,
    phone character varying(20),
    address1 character varying(255),
    address2 character varying(255),
    city character varying(100),
    state character varying(100),
    zip_code character varying(20),
    country character varying(100),
    employee_number character varying(50) NOT NULL,
    hire_date date NOT NULL,
    position_id uuid,
    department_id uuid,
    manager_id uuid
);


ALTER TABLE public.employees OWNER TO crm_user;

--
-- Name: positions; Type: TABLE; Schema: public; Owner: crm_user
--

CREATE TABLE public.positions (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    code character varying(50) NOT NULL,
    level integer,
    description text,
    department_id uuid,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_at timestamp without time zone,
    created_by_id uuid,
    updated_by_id uuid
);


ALTER TABLE public.positions OWNER TO crm_user;

--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: employees pk_employees; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT pk_employees PRIMARY KEY (id);


--
-- Name: positions pk_positions; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.positions
    ADD CONSTRAINT pk_positions PRIMARY KEY (id);


--
-- Name: employees uq_employees_email; Type: CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT uq_employees_email UNIQUE (email);


--
-- Name: ix_employees_department_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_employees_department_id ON public.employees USING btree (department_id);


--
-- Name: ix_employees_employee_number; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE UNIQUE INDEX ix_employees_employee_number ON public.employees USING btree (employee_number);


--
-- Name: ix_employees_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_employees_id ON public.employees USING btree (id);


--
-- Name: ix_employees_is_deleted; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_employees_is_deleted ON public.employees USING btree (is_deleted);


--
-- Name: ix_employees_manager_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_employees_manager_id ON public.employees USING btree (manager_id);


--
-- Name: ix_employees_position_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_employees_position_id ON public.employees USING btree (position_id);


--
-- Name: ix_positions_code; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_positions_code ON public.positions USING btree (code);


--
-- Name: ix_positions_department_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_positions_department_id ON public.positions USING btree (department_id);


--
-- Name: ix_positions_id; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_positions_id ON public.positions USING btree (id);


--
-- Name: ix_positions_is_active; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_positions_is_active ON public.positions USING btree (is_active);


--
-- Name: ix_positions_is_deleted; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_positions_is_deleted ON public.positions USING btree (is_deleted);


--
-- Name: ix_positions_level; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_positions_level ON public.positions USING btree (level);


--
-- Name: ix_positions_name; Type: INDEX; Schema: public; Owner: crm_user
--

CREATE INDEX ix_positions_name ON public.positions USING btree (name);


--
-- Name: employees fk_employees_position_id_positions; Type: FK CONSTRAINT; Schema: public; Owner: crm_user
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT fk_employees_position_id_positions FOREIGN KEY (position_id) REFERENCES public.positions(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

