import streamlit as st
import pandas as pd
from PIL import Image
import io
import bcrypt
from sqlalchemy import create_engine, Column, Integer, String, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuración de la base de datos
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer)
    author_name = Column(String)
    case_description = Column(Text)
    image = Column(LargeBinary)

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer)
    author_id = Column(Integer)
    author_name = Column(String)
    content = Column(Text)

engine = create_engine('sqlite:///health_social_network.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Función para registrar un nuevo usuario
def register_user(username, password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    new_user = User(username=username, password=hashed_password)
    session.add(new_user)
    session.commit()

# Función para verificar el inicio de sesión de un usuario
def login_user(username, password):
    user = session.query(User).filter_by(username=username).first()
    if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
        return user
    return None

# Función para agregar un nuevo caso clínico
def add_post(author_id, author_name, case_description, image):
    new_post = Post(author_id=author_id, author_name=author_name, case_description=case_description, image=image)
    session.add(new_post)
    session.commit()

# Función para agregar un comentario
def add_comment(post_id, author_id, author_name, content):
    new_comment = Comment(post_id=post_id, author_id=author_id, author_name=author_name, content=content)
    session.add(new_comment)
    session.commit()

# Inicialización de session_state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

# Título de la aplicación
st.title("Red Social para Profesionales de la Salud")

# Autenticación y registro de usuarios
if not st.session_state['authenticated']:
    st.sidebar.header("Autenticación")
    username = st.sidebar.text_input("Nombre de usuario")
    password = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Iniciar sesión"):
        user = login_user(username, password)
        if user:
            st.session_state['authenticated'] = True
            st.session_state['user_id'] = user.id
            st.session_state['username'] = user.username
            st.sidebar.success("Inicio de sesión exitoso")
        else:
            st.sidebar.error("Nombre de usuario o contraseña incorrectos")
    if st.sidebar.button("Registrarse"):
        if username and password:
            register_user(username, password)
            st.sidebar.success("Usuario registrado con éxito")
        else:
            st.sidebar.error("Por favor, ingrese un nombre de usuario y una contraseña.")
else:
    st.sidebar.success(f"Autenticado como {st.session_state['username']}")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state['authenticated'] = False
        st.session_state['user_id'] = None
        st.session_state['username'] = None
        st.experimental_rerun()

# Formulario para añadir un nuevo caso clínico
if st.session_state['authenticated']:
    st.sidebar.header("Publicar un nuevo caso clínico")
    with st.sidebar.form("new_post_form"):
        case_description = st.text_area("Descripción del caso clínico")
        uploaded_file = st.file_uploader("Subir imagen del caso clínico", type=["jpg", "jpeg", "png"])
        submit_button = st.form_submit_button(label="Publicar")

        if submit_button:
            if case_description and uploaded_file:
                image = uploaded_file.read()
                add_post(st.session_state['user_id'], st.session_state['username'], case_description, image)
                st.sidebar.success("Caso clínico publicado con éxito!")
            else:
                st.sidebar.error("Por favor, completa todos los campos y sube una imagen.")

# Mostrar todos los casos clínicos publicados
st.header("Casos Clínicos Publicados")
posts = session.query(Post).all()
for post in posts:
    st.subheader(post.author_name)
    st.text(post.case_description)
    image = Image.open(io.BytesIO(post.image))
    st.image(image)

    # Mostrar comentarios
    comments = session.query(Comment).filter_by(post_id=post.id).all()
    st.subheader("Comentarios")
    for comment in comments:
        st.text(f"{comment.author_name}: {comment.content}")

    # Formulario para añadir un nuevo comentario
    if st.session_state['authenticated']:
        with st.form(f"new_comment_form_{post.id}"):
            comment_content = st.text_input("Escribe un comentario")
            submit_comment_button = st.form_submit_button(label="Comentar")
            if submit_comment_button:
                if comment_content:
                    add_comment(post.id, st.session_state['user_id'], st.session_state['username'], comment_content)
                    st.success("Comentario publicado con éxito!")
                    st.experimental_rerun()
                else:
                    st.error("El comentario no puede estar vacío.")
