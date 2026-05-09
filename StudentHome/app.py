import os
import re
import io
import math
from datetime import date, datetime, timedelta
from functools import wraps

from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, text
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_MEDIA_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "mp4", "webm", "mov"}
VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}
PROFILE_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_ANNONCE_MEDIA = 20
ADMIN_EMAIL = "redakouchtam@icloud.com"
ADMIN_DEFAULT_PASSWORD = "Admin@12345"
SUPPORTED_LANGUAGES = {"fr", "en", "ar"}


def load_env_file():
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()

from config import Config


def fix_text_encoding(value):
    if not isinstance(value, str) or not any(marker in value for marker in ("Ã", "â", "Ø", "Ù", "Ă", "Â")):
        return value
    for encoding in ("cp1252", "latin1"):
        try:
            return value.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
    return value

FACULTES_UCA = {
    "FSSM": {"nom": "Faculte des Sciences Semlalia", "lat": 31.64931, "lng": -8.01571},
    "FSJES": {"nom": "Faculte des Sciences Juridiques, Economiques et Sociales", "lat": 31.66438, "lng": -7.99928},
    "FLSH": {"nom": "Faculte des Lettres et des Sciences Humaines", "lat": 31.66682, "lng": -7.99794},
    "FMPM": {"nom": "Faculte de Medecine et de Pharmacie", "lat": 31.641944, "lng": -8.013032},
    "FST": {"nom": "Faculte des Sciences et Techniques de Gueliz", "lat": 31.64418, "lng": -8.02108},
    "ENCG": {"nom": "Ecole Nationale de Commerce et de Gestion", "lat": 31.652, "lng": -8.002},
    "ENSA": {"nom": "Ecole Nationale des Sciences Appliquees", "lat": 31.64718, "lng": -8.02118},
    "ENS": {"nom": "Ecole Normale Superieure", "lat": 31.6281517, "lng": -8.0503661},
}

QUARTIER_COORDS = {
    "Semlalia": (31.6586, -8.0205),
    "Daoudiate": (31.6547, -8.0005),
    "Gueliz": (31.6346, -8.0093),
    "M'Hamid": (31.5798, -8.0364),
    "Massira": (31.6466, -8.0848),
    "Sidi Abbad": (31.6531, -8.0278),
    "Amerchich": (31.6708, -8.0141),
    "Bab Doukkala": (31.6357, -7.9994),
    "Hivernage": (31.6218, -8.0114),
    "Medina": (31.6258, -7.9891),
    "Route de Safi": (31.6790, -8.0400),
    "Route de Casablanca": (31.6862, -8.0068),
    "Targa": (31.6700, -8.0605),
}

TRANSLATIONS = {
    "fr": {
        "nav_housing": "Logements",
        "nav_dashboard": "Dashboard",
        "nav_reservations": "RÃ©servations",
        "nav_messages": "Messagerie",
        "nav_help": "Aide",
        "nav_profile": "Profil",
        "nav_add": "Ajouter",
        "nav_admin": "Admin",
        "nav_logout": "DÃ©connexion",
        "nav_login": "Connexion",
        "nav_register": "Inscription",
        "nav_home": "Accueil",
        "nav_favorites": "Favoris",
        "nav_colocation": "Colocation",
        "nav_vault": "Coffre-fort",
        "budget_recommendation": "Budget recommande",
        "min_rooms": "Chambres minimum",
        "floor": "Etage",
        "max_distance_faculty": "Distance max faculte (km)",
        "colocation_only": "Colocation uniquement",
        "interactive_map": "Carte interactive",
        "show_map": "Afficher la carte",
        "recommended_housing": "Logements recommandes pour vous",
        "contract": "Contrat",
        "no_action": "Aucune action",
        "university_year": "Annee universitaire",
        "smoker": "Fumeur",
        "budget": "Budget",
        "roommate_space": "Espace colocation",
        "roommate_profile": "Mon profil colocation",
        "compatible_profiles": "Profils compatibles",
        "roommate_budget_calculator": "Calculateur budget colocation",
        "footer": "StudentHome - Plateforme de logement Ã©tudiant pour l'UCA",
        "hero_tag": "Logement Ã©tudiant UCA",
        "hero_title": "Trouvez un logement proche de votre facultÃ©.",
        "hero_text": "StudentHome aide les Ã©tudiants Ã  chercher, rÃ©server et suivre leur demande en toute simplicitÃ©.",
        "explore_housing": "Explorer les logements",
        "create_account": "CrÃ©er un compte",
        "popular_housing": "Logements populaires",
        "view_all": "Tout voir",
        "no_listing_title": "Aucune annonce disponible pour le moment",
        "no_listing_text": "Les logements apparaÃ®tront ici dÃ¨s quâ€™un propriÃ©taire publiera sa premiÃ¨re annonce.",
        "create_owner_account": "CrÃ©er un compte propriÃ©taire",
        "for_students": "Pour Ã©tudiants",
        "for_students_text": "Recherche par facultÃ©, quartier, prix, rÃ©servation, suivi des demandes et avis.",
        "for_owners": "Pour propriÃ©taires",
        "for_owners_text": "Publication d'annonces, gestion des demandes et validation de conformitÃ©.",
        "choose_role_title": "Choisissez votre type de compte",
        "choose_role_text": "SÃ©lectionnez le profil qui correspond Ã  votre utilisation de StudentHome.",
        "student": "Ã‰tudiant",
        "owner": "PropriÃ©taire",
        "student_choice_text": "Rechercher un logement, contacter un propriÃ©taire et suivre vos rÃ©servations.",
        "owner_choice_text": "Publier vos annonces, rÃ©pondre aux Ã©tudiants et gÃ©rer vos demandes.",
        "continue": "Continuer",
        "register_title": "Inscription",
        "login_title": "Connexion",
        "full_name": "Nom complet",
        "email": "Email",
        "password": "Mot de passe",
        "faculty": "FacultÃ© UCA",
        "massar_code": "Code Massar",
        "phone": "TÃ©lÃ©phone",
        "create_the_account": "CrÃ©er le compte",
        "identifier": "Identifiant",
        "login_button": "Se connecter",
        "login_continue_text": "Connectez-vous pour continuer votre action.",
        "login_identifier_placeholder": "Code Massar Ã©tudiant ou email",
        "forgot_password": "Mot de passe oubliÃ© ?",
        "create_student_account": "CrÃ©er un compte Ã©tudiant",
        "change": "Changer",
        "register_continue_text": "CrÃ©ez votre compte pour continuer votre action sur StudentHome.",
        "strong_password_placeholder": "8 caractÃ¨res, majuscule, minuscule, chiffre, spÃ©cial",
        "massar_example": "Exemple : G123456789",
        "profile_title": "Mon profil",
        "profile_hint": "Votre email reste verrouillÃ©. Vous pouvez modifier les autres informations de votre compte.",
        "profile_photo": "Photo de profil",
        "profile_photo_hint": "Ajoutez une image JPG, PNG ou WEBP. Si vous ne choisissez rien, l'avatar actuel reste gardÃ©.",
        "change_password": "Changer le mot de passe",
        "keep_password_hint": "Laissez ces champs vides si vous souhaitez garder votre mot de passe actuel.",
        "new_password": "Nouveau mot de passe",
        "confirm_password": "Confirmer le mot de passe",
        "password_min_placeholder": "8 caractÃ¨res minimum",
        "repeat_password_placeholder": "Retapez le mot de passe",
        "save_changes": "Enregistrer les modifications",
        "search_housing_title": "Rechercher un logement",
        "search_placeholder": "Tapez une recherche : quartier, facultÃ©, titre...",
        "filter": "Filtrer",
        "search": "Rechercher",
        "sector_marrakech": "Secteur Ã  Marrakech",
        "all_sectors": "Tous les secteurs",
        "min_price": "Prix min",
        "max_price": "Prix max",
        "housing_type": "Type de logement",
        "all_types": "Tous les types",
        "near_faculty": "FacultÃ© proche",
        "available_only": "Disponible uniquement",
        "reset": "RÃ©initialiser",
        "apply_filters": "Appliquer les filtres",
        "no_listing_now": "Aucune annonce pour lâ€™instant",
        "no_listing_long": "Il nâ€™y a encore aucun logement publiÃ© sur StudentHome. DÃ¨s quâ€™un propriÃ©taire ajoute une annonce, elle sera affichÃ©e ici.",
        "publish_first_listing": "Publier la premiÃ¨re annonce",
        "available_from": "Disponible Ã  partir du",
        "available": "Disponible",
        "unavailable": "Indisponible",
        "view_details": "Voir dÃ©tails",
        "close_to": "proche",
        "month": "mois",
        "table_housing": "Logement",
        "table_date": "Date",
        "table_amount": "Montant",
        "table_payment": "Paiement",
        "table_reservation": "RÃ©servation",
        "table_actions": "Actions",
        "pay": "Payer",
        "review": "Avis",
        "no_reservation": "Aucune rÃ©servation.",
        "messages_title": "Mes discussions",
        "view_housing": "Voir les logements",
        "discussions": "Discussions",
        "no_discussion_title": "Aucune discussion pour le moment",
        "no_discussion_text": "Les conversations apparaÃ®tront ici aprÃ¨s un premier message envoyÃ© depuis une annonce.",
        "chat_preview_text": "SÃ©lectionnez une discussion pour consulter les messages et rÃ©pondre comme dans une messagerie instantanÃ©e.",
        "owner_label": "PropriÃ©taire",
        "student_label": "Ã‰tudiant",
        "all_discussions": "Toutes les discussions",
        "conversation": "Conversation",
        "back": "Retour",
        "no_message_discussion": "Aucun message dans cette discussion.",
        "write_message": "Ã‰crire un message...",
        "send": "Envoyer",
        "help_title": "Besoin dâ€™aide ?",
        "help_text": "Ã‰crivez une demande dâ€™aide, une remarque ou un commentaire. Votre nom et votre email seront ajoutÃ©s automatiquement depuis votre compte.",
        "name": "Nom",
        "subject": "Sujet",
        "help_subject_placeholder": "Exemple : ProblÃ¨me de rÃ©servation",
        "message_or_comment": "Message ou commentaire",
        "help_message_placeholder": "DÃ©crivez votre demande...",
        "send_request": "Envoyer la demande",
    },
    "en": {
        "nav_housing": "Housing",
        "nav_dashboard": "Dashboard",
        "nav_reservations": "Reservations",
        "nav_messages": "Messages",
        "nav_help": "Help",
        "nav_profile": "Profile",
        "nav_add": "Add",
        "nav_admin": "Admin",
        "nav_logout": "Logout",
        "nav_login": "Login",
        "nav_register": "Sign up",
        "nav_home": "Home",
        "nav_favorites": "Favorites",
        "nav_colocation": "Roommates",
        "nav_vault": "Digital vault",
        "budget_recommendation": "Recommended budget",
        "min_rooms": "Minimum rooms",
        "floor": "Floor",
        "max_distance_faculty": "Max distance to faculty (km)",
        "colocation_only": "Roommate housing only",
        "interactive_map": "Interactive map",
        "show_map": "Show map",
        "recommended_housing": "Recommended housing for you",
        "contract": "Contract",
        "no_action": "No action",
        "university_year": "University year",
        "smoker": "Smoker",
        "budget": "Budget",
        "roommate_space": "Roommate space",
        "roommate_profile": "My roommate profile",
        "compatible_profiles": "Compatible profiles",
        "roommate_budget_calculator": "Roommate budget calculator",
        "footer": "StudentHome - Student housing platform for UCA",
        "hero_tag": "UCA student housing",
        "hero_title": "Find housing close to your faculty.",
        "hero_text": "StudentHome helps students search, reserve and track their requests with ease.",
        "explore_housing": "Explore housing",
        "create_account": "Create account",
        "popular_housing": "Popular housing",
        "view_all": "View all",
        "no_listing_title": "No listings available yet",
        "no_listing_text": "Housing listings will appear here as soon as an owner publishes the first listing.",
        "create_owner_account": "Create owner account",
        "for_students": "For students",
        "for_students_text": "Search by faculty, area, price, reservation tracking and reviews.",
        "for_owners": "For owners",
        "for_owners_text": "Publish listings, manage requests and confirm housing conformity.",
        "choose_role_title": "Choose your account type",
        "choose_role_text": "Select the profile that matches how you want to use StudentHome.",
        "student": "Student",
        "owner": "Owner",
        "student_choice_text": "Search housing, contact owners and track your reservations.",
        "owner_choice_text": "Publish listings, reply to students and manage requests.",
        "continue": "Continue",
        "register_title": "Sign up",
        "login_title": "Login",
        "full_name": "Full name",
        "email": "Email",
        "password": "Password",
        "faculty": "UCA faculty",
        "massar_code": "Massar code",
        "phone": "Phone",
        "create_the_account": "Create account",
        "identifier": "Identifier",
        "login_button": "Login",
        "login_continue_text": "Log in to continue your action.",
        "login_identifier_placeholder": "Student Massar code or email",
        "forgot_password": "Forgot password?",
        "create_student_account": "Create student account",
        "change": "Change",
        "register_continue_text": "Create your account to continue your action on StudentHome.",
        "strong_password_placeholder": "8 characters, uppercase, lowercase, number, special",
        "massar_example": "Example: G123456789",
        "profile_title": "My profile",
        "profile_hint": "Your email stays locked. You can edit the other information in your account.",
        "profile_photo": "Profile photo",
        "profile_photo_hint": "Add a JPG, PNG or WEBP image. If you choose nothing, the current avatar is kept.",
        "change_password": "Change password",
        "keep_password_hint": "Leave these fields empty if you want to keep your current password.",
        "new_password": "New password",
        "confirm_password": "Confirm password",
        "password_min_placeholder": "8 characters minimum",
        "repeat_password_placeholder": "Retype the password",
        "save_changes": "Save changes",
        "search_housing_title": "Search housing",
        "search_placeholder": "Type a search: area, faculty, title...",
        "filter": "Filter",
        "search": "Search",
        "sector_marrakech": "Area in Marrakech",
        "all_sectors": "All areas",
        "min_price": "Min price",
        "max_price": "Max price",
        "housing_type": "Housing type",
        "all_types": "All types",
        "near_faculty": "Nearby faculty",
        "available_only": "Available only",
        "reset": "Reset",
        "apply_filters": "Apply filters",
        "no_listing_now": "No listing yet",
        "no_listing_long": "No housing has been published on StudentHome yet. As soon as an owner adds a listing, it will appear here.",
        "publish_first_listing": "Publish the first listing",
        "available_from": "Available from",
        "available": "Available",
        "unavailable": "Unavailable",
        "view_details": "View details",
        "close_to": "near",
        "month": "month",
        "table_housing": "Housing",
        "table_date": "Date",
        "table_amount": "Amount",
        "table_payment": "Payment",
        "table_reservation": "Reservation",
        "table_actions": "Actions",
        "pay": "Pay",
        "review": "Review",
        "no_reservation": "No reservation.",
        "messages_title": "My discussions",
        "view_housing": "View housing",
        "discussions": "Discussions",
        "no_discussion_title": "No discussion yet",
        "no_discussion_text": "Conversations will appear here after a first message is sent from a listing.",
        "chat_preview_text": "Select a discussion to view messages and reply like in instant messaging.",
        "owner_label": "Owner",
        "student_label": "Student",
        "all_discussions": "All discussions",
        "conversation": "Conversation",
        "back": "Back",
        "no_message_discussion": "No message in this discussion.",
        "write_message": "Write a message...",
        "send": "Send",
        "help_title": "Need help?",
        "help_text": "Write a help request, note or comment. Your name and email will be added automatically from your account.",
        "name": "Name",
        "subject": "Subject",
        "help_subject_placeholder": "Example: Reservation issue",
        "message_or_comment": "Message or comment",
        "help_message_placeholder": "Describe your request...",
        "send_request": "Send request",
    },
    "ar": {
        "nav_housing": "Ø§Ù„Ø³ÙƒÙ†",
        "nav_dashboard": "Ù„ÙˆØ­Ø© Ø§Ù„ØªØ­ÙƒÙ…",
        "nav_reservations": "Ø§Ù„Ø­Ø¬ÙˆØ²Ø§Øª",
        "nav_messages": "Ø§Ù„Ø±Ø³Ø§Ø¦Ù„",
        "nav_help": "Ù…Ø³Ø§Ø¹Ø¯Ø©",
        "nav_add": "Ø¥Ø¶Ø§ÙØ©",
        "nav_admin": "Ø§Ù„Ø¥Ø¯Ø§Ø±Ø©",
        "nav_logout": "Ø®Ø±ÙˆØ¬",
        "nav_login": "Ø¯Ø®ÙˆÙ„",
        "nav_register": "ØªØ³Ø¬ÙŠÙ„",
        "nav_home": "Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ©",
        "nav_favorites": "Ø§Ù„Ù…ÙØ¶Ù„Ø©",
        "nav_colocation": "Ø§Ù„Ø³ÙƒÙ† Ø§Ù„Ù…Ø´ØªØ±Ùƒ",
        "nav_vault": "Ø§Ù„Ø®Ø²Ù†Ø© Ø§Ù„Ø±Ù‚Ù…ÙŠØ©",
        "budget_recommendation": "Ø§Ù„Ù…ÙŠØ²Ø§Ù†ÙŠØ© Ø§Ù„Ù…Ù‚ØªØ±Ø­Ø©",
        "min_rooms": "Ø£Ù‚Ù„ Ø¹Ø¯Ø¯ Ø§Ù„ØºØ±Ù",
        "floor": "Ø§Ù„Ø·Ø§Ø¨Ù‚",
        "max_distance_faculty": "Ø£Ù‚ØµÙ‰ Ù…Ø³Ø§ÙØ© Ø¹Ù† Ø§Ù„ÙƒÙ„ÙŠØ© (ÙƒÙ…) ",
        "colocation_only": "Ø§Ù„Ø³ÙƒÙ† Ø§Ù„Ù…Ø´ØªØ±Ùƒ ÙÙ‚Ø·",
        "interactive_map": "Ø®Ø±ÙŠØ·Ø© ØªÙØ§Ø¹Ù„ÙŠØ©",
        "show_map": "Ø¥Ø¸Ù‡Ø§Ø± Ø§Ù„Ø®Ø±ÙŠØ·Ø©",
        "recommended_housing": "Ø³ÙƒÙ† Ù…Ù‚ØªØ±Ø­ Ù„Ùƒ",
        "contract": "Ø¹Ù‚Ø¯",
        "no_action": "Ù„Ø§ Ø¥Ø¬Ø±Ø§Ø¡",
        "university_year": "Ø§Ù„Ø³Ù†Ø© Ø§Ù„Ø¬Ø§Ù…Ø¹ÙŠØ©",
        "smoker": "Ù…Ø¯Ø®Ù†",
        "budget": "Ø§Ù„Ù…ÙŠØ²Ø§Ù†ÙŠØ©",
        "roommate_space": "ÙØ¶Ø§Ø¡ Ø§Ù„Ø³ÙƒÙ† Ø§Ù„Ù…Ø´ØªØ±Ùƒ",
        "roommate_profile": "Ù…Ù„ÙÙŠ Ù„Ù„Ø³ÙƒÙ† Ø§Ù„Ù…Ø´ØªØ±Ùƒ",
        "compatible_profiles": "Ù…Ù„ÙØ§Øª Ù…ØªÙˆØ§ÙÙ‚Ø©",
        "roommate_budget_calculator": "Ø­Ø§Ø³Ø¨Ø© Ù…ÙŠØ²Ø§Ù†ÙŠØ© Ø§Ù„Ø³ÙƒÙ† Ø§Ù„Ù…Ø´ØªØ±Ùƒ",
        "footer": "StudentHome - Ù…Ù†ØµØ© Ø§Ù„Ø³ÙƒÙ† Ø§Ù„Ø·Ù„Ø§Ø¨ÙŠ Ù„Ø¬Ø§Ù…Ø¹Ø© Ø§Ù„Ù‚Ø§Ø¶ÙŠ Ø¹ÙŠØ§Ø¶",
        "hero_tag": "Ø³ÙƒÙ† Ø·Ù„Ø§Ø¨ Ø¬Ø§Ù…Ø¹Ø© Ø§Ù„Ù‚Ø§Ø¶ÙŠ Ø¹ÙŠØ§Ø¶",
        "hero_title": "Ø§Ø¹Ø«Ø± Ø¹Ù„Ù‰ Ø³ÙƒÙ† Ù‚Ø±ÙŠØ¨ Ù…Ù† ÙƒÙ„ÙŠØªÙƒ.",
        "hero_text": "ÙŠØ³Ø§Ø¹Ø¯ StudentHome Ø§Ù„Ø·Ù„Ø§Ø¨ Ø¹Ù„Ù‰ Ø§Ù„Ø¨Ø­Ø« ÙˆØ§Ù„Ø­Ø¬Ø² ÙˆØªØªØ¨Ø¹ Ø§Ù„Ø·Ù„Ø¨Ø§Øª Ø¨Ø³Ù‡ÙˆÙ„Ø©.",
        "explore_housing": "Ø§Ø³ØªÙƒØ´Ø§Ù Ø§Ù„Ø³ÙƒÙ†",
        "create_account": "Ø¥Ù†Ø´Ø§Ø¡ Ø­Ø³Ø§Ø¨",
        "popular_housing": "Ø¥Ø¹Ù„Ø§Ù†Ø§Øª Ù…Ù…ÙŠØ²Ø©",
        "view_all": "Ø¹Ø±Ø¶ Ø§Ù„ÙƒÙ„",
        "no_listing_title": "Ù„Ø§ ØªÙˆØ¬Ø¯ Ø¥Ø¹Ù„Ø§Ù†Ø§Øª Ø­Ø§Ù„ÙŠØ§",
        "no_listing_text": "Ø³ØªØ¸Ù‡Ø± Ø§Ù„Ø¥Ø¹Ù„Ø§Ù†Ø§Øª Ù‡Ù†Ø§ Ø¹Ù†Ø¯Ù…Ø§ ÙŠÙ†Ø´Ø± Ø£ÙˆÙ„ Ù…Ø§Ù„Ùƒ Ø¥Ø¹Ù„Ø§Ù†Ù‡.",
        "create_owner_account": "Ø¥Ù†Ø´Ø§Ø¡ Ø­Ø³Ø§Ø¨ Ù…Ø§Ù„Ùƒ",
        "for_students": "Ù„Ù„Ø·Ù„Ø§Ø¨",
        "for_students_text": "Ø§Ù„Ø¨Ø­Ø« Ø­Ø³Ø¨ Ø§Ù„ÙƒÙ„ÙŠØ©ØŒ Ø§Ù„Ø­ÙŠØŒ Ø§Ù„Ø³Ø¹Ø±ØŒ Ø§Ù„Ø­Ø¬Ø²ØŒ ØªØªØ¨Ø¹ Ø§Ù„Ø·Ù„Ø¨Ø§Øª ÙˆØ§Ù„ØªÙ‚ÙŠÙŠÙ…Ø§Øª.",
        "for_owners": "Ù„Ù„Ù…Ø§Ù„ÙƒÙŠÙ†",
        "for_owners_text": "Ù†Ø´Ø± Ø§Ù„Ø¥Ø¹Ù„Ø§Ù†Ø§ØªØŒ Ø¥Ø¯Ø§Ø±Ø© Ø§Ù„Ø·Ù„Ø¨Ø§Øª ÙˆØªØ£ÙƒÙŠØ¯ Ù…Ø·Ø§Ø¨Ù‚Ø© Ø§Ù„Ø³ÙƒÙ†.",
        "choose_role_title": "Ø§Ø®ØªØ± Ù†ÙˆØ¹ Ø§Ù„Ø­Ø³Ø§Ø¨",
        "choose_role_text": "Ø§Ø®ØªØ± Ø§Ù„Ù…Ù„Ù Ø§Ù„Ù…Ù†Ø§Ø³Ø¨ Ù„Ø§Ø³ØªØ®Ø¯Ø§Ù…Ùƒ Ù„Ù…Ù†ØµØ© StudentHome.",
        "student": "Ø·Ø§Ù„Ø¨",
        "owner": "Ù…Ø§Ù„Ùƒ",
        "student_choice_text": "Ø§Ø¨Ø­Ø« Ø¹Ù† Ø§Ù„Ø³ÙƒÙ†ØŒ ØªÙˆØ§ØµÙ„ Ù…Ø¹ Ø§Ù„Ù…Ø§Ù„ÙƒÙŠÙ† ÙˆØªØªØ¨Ø¹ Ø­Ø¬ÙˆØ²Ø§ØªÙƒ.",
        "owner_choice_text": "Ø§Ù†Ø´Ø± Ø¥Ø¹Ù„Ø§Ù†Ø§ØªÙƒØŒ Ø£Ø¬Ø¨ Ø§Ù„Ø·Ù„Ø§Ø¨ ÙˆÙ‚Ù… Ø¨Ø¥Ø¯Ø§Ø±Ø© Ø§Ù„Ø·Ù„Ø¨Ø§Øª.",
        "continue": "Ù…ØªØ§Ø¨Ø¹Ø©",
        "register_title": "ØªØ³Ø¬ÙŠÙ„",
        "login_title": "Ø¯Ø®ÙˆÙ„",
        "full_name": "Ø§Ù„Ø§Ø³Ù… Ø§Ù„ÙƒØ§Ù…Ù„",
        "email": "Ø§Ù„Ø¨Ø±ÙŠØ¯ Ø§Ù„Ø¥Ù„ÙƒØªØ±ÙˆÙ†ÙŠ",
        "password": "ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±",
        "faculty": "ÙƒÙ„ÙŠØ© UCA",
        "massar_code": "Ø±Ù…Ø² Ù…Ø³Ø§Ø±",
        "phone": "Ø§Ù„Ù‡Ø§ØªÙ",
        "create_the_account": "Ø¥Ù†Ø´Ø§Ø¡ Ø§Ù„Ø­Ø³Ø§Ø¨",
        "identifier": "Ø§Ù„Ù…Ø¹Ø±Ù‘Ù",
        "login_button": "Ø¯Ø®ÙˆÙ„",
        "login_continue_text": "Ø³Ø¬Ù„ Ø§Ù„Ø¯Ø®ÙˆÙ„ Ù„Ù…ØªØ§Ø¨Ø¹Ø© Ø§Ù„Ø¹Ù…Ù„ÙŠØ©.",
        "login_identifier_placeholder": "Ø±Ù…Ø² Ù…Ø³Ø§Ø± Ù„Ù„Ø·Ø§Ù„Ø¨ Ø£Ùˆ Ø§Ù„Ø¨Ø±ÙŠØ¯ Ø§Ù„Ø¥Ù„ÙƒØªØ±ÙˆÙ†ÙŠ",
        "forgot_password": "Ù†Ø³ÙŠØª ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±ØŸ",
        "create_student_account": "Ø¥Ù†Ø´Ø§Ø¡ Ø­Ø³Ø§Ø¨ Ø·Ø§Ù„Ø¨",
        "change": "ØªØºÙŠÙŠØ±",
        "register_continue_text": "Ø£Ù†Ø´Ø¦ Ø­Ø³Ø§Ø¨Ùƒ Ù„Ù…ØªØ§Ø¨Ø¹Ø© Ø§Ù„Ø¹Ù…Ù„ÙŠØ© Ø¹Ù„Ù‰ StudentHome.",
        "strong_password_placeholder": "8 Ø£Ø­Ø±ÙØŒ Ø­Ø±Ù ÙƒØ¨ÙŠØ±ØŒ Ø­Ø±Ù ØµØºÙŠØ±ØŒ Ø±Ù‚Ù…ØŒ Ø±Ù…Ø² Ø®Ø§Øµ",
        "massar_example": "Ù…Ø«Ø§Ù„: G123456789",
        "profile_title": "Ù…Ù„ÙÙŠ Ø§Ù„Ø´Ø®ØµÙŠ",
        "profile_hint": "ÙŠØ¨Ù‚Ù‰ Ø¨Ø±ÙŠØ¯Ùƒ Ø§Ù„Ø¥Ù„ÙƒØªØ±ÙˆÙ†ÙŠ Ù…Ù‚ÙÙ„Ø§. ÙŠÙ…ÙƒÙ†Ùƒ ØªØ¹Ø¯ÙŠÙ„ Ø¨Ø§Ù‚ÙŠ Ù…Ø¹Ù„ÙˆÙ…Ø§Øª Ø­Ø³Ø§Ø¨Ùƒ.",
        "profile_photo": "ØµÙˆØ±Ø© Ø§Ù„Ù…Ù„Ù Ø§Ù„Ø´Ø®ØµÙŠ",
        "profile_photo_hint": "Ø£Ø¶Ù ØµÙˆØ±Ø© JPG Ø£Ùˆ PNG Ø£Ùˆ WEBP. Ø¥Ø°Ø§ Ù„Ù… ØªØ®ØªØ± Ø´ÙŠØ¦Ø§ ÙØ³ÙŠØ¨Ù‚Ù‰ Ø§Ù„Ø±Ù…Ø² Ø§Ù„Ø­Ø§Ù„ÙŠ.",
        "change_password": "ØªØºÙŠÙŠØ± ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±",
        "keep_password_hint": "Ø§ØªØ±Ùƒ Ù‡Ø°Ù‡ Ø§Ù„Ø®Ø§Ù†Ø§Øª ÙØ§Ø±ØºØ© Ø¥Ø°Ø§ Ø£Ø±Ø¯Øª Ø§Ù„Ø§Ø­ØªÙØ§Ø¸ Ø¨ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ± Ø§Ù„Ø­Ø§Ù„ÙŠØ©.",
        "new_password": "ÙƒÙ„Ù…Ø© Ù…Ø±ÙˆØ± Ø¬Ø¯ÙŠØ¯Ø©",
        "confirm_password": "ØªØ£ÙƒÙŠØ¯ ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±",
        "password_min_placeholder": "8 Ø£Ø­Ø±Ù Ø¹Ù„Ù‰ Ø§Ù„Ø£Ù‚Ù„",
        "repeat_password_placeholder": "Ø£Ø¹Ø¯ ÙƒØªØ§Ø¨Ø© ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±",
        "save_changes": "Ø­ÙØ¸ Ø§Ù„ØªØ¹Ø¯ÙŠÙ„Ø§Øª",
        "search_housing_title": "Ø§Ù„Ø¨Ø­Ø« Ø¹Ù† Ø³ÙƒÙ†",
        "search_placeholder": "Ø§ÙƒØªØ¨ Ø¨Ø­Ø«Ø§: Ø§Ù„Ø­ÙŠØŒ Ø§Ù„ÙƒÙ„ÙŠØ©ØŒ Ø§Ù„Ø¹Ù†ÙˆØ§Ù†...",
        "filter": "ØªØµÙÙŠØ©",
        "search": "Ø¨Ø­Ø«",
        "sector_marrakech": "Ø§Ù„Ø­ÙŠ ÙÙŠ Ù…Ø±Ø§ÙƒØ´",
        "all_sectors": "ÙƒÙ„ Ø§Ù„Ø£Ø­ÙŠØ§Ø¡",
        "min_price": "Ø£Ù‚Ù„ Ø³Ø¹Ø±",
        "max_price": "Ø£Ø¹Ù„Ù‰ Ø³Ø¹Ø±",
        "housing_type": "Ù†ÙˆØ¹ Ø§Ù„Ø³ÙƒÙ†",
        "all_types": "ÙƒÙ„ Ø§Ù„Ø£Ù†ÙˆØ§Ø¹",
        "near_faculty": "Ø§Ù„ÙƒÙ„ÙŠØ© Ø§Ù„Ù‚Ø±ÙŠØ¨Ø©",
        "available_only": "Ø§Ù„Ù…ØªØ§Ø­ ÙÙ‚Ø·",
        "reset": "Ø¥Ø¹Ø§Ø¯Ø© Ø¶Ø¨Ø·",
        "apply_filters": "ØªØ·Ø¨ÙŠÙ‚ Ø§Ù„ÙÙ„Ø§ØªØ±",
        "no_listing_now": "Ù„Ø§ ØªÙˆØ¬Ø¯ Ø¥Ø¹Ù„Ø§Ù†Ø§Øª Ø­Ø§Ù„ÙŠØ§",
        "no_listing_long": "Ù„Ù… ÙŠØªÙ… Ù†Ø´Ø± Ø£ÙŠ Ø³ÙƒÙ† Ø¹Ù„Ù‰ StudentHome Ø¨Ø¹Ø¯. Ø¹Ù†Ø¯Ù…Ø§ ÙŠØ¶ÙŠÙ Ù…Ø§Ù„Ùƒ Ø¥Ø¹Ù„Ø§Ù†Ø§ Ø³ÙŠØ¸Ù‡Ø± Ù‡Ù†Ø§.",
        "publish_first_listing": "Ù†Ø´Ø± Ø£ÙˆÙ„ Ø¥Ø¹Ù„Ø§Ù†",
        "available_from": "Ù…ØªØ§Ø­ Ø§Ø¨ØªØ¯Ø§Ø¡ Ù…Ù†",
        "available": "Ù…ØªØ§Ø­",
        "unavailable": "ØºÙŠØ± Ù…ØªØ§Ø­",
        "view_details": "Ø¹Ø±Ø¶ Ø§Ù„ØªÙØ§ØµÙŠÙ„",
        "close_to": "Ù‚Ø±ÙŠØ¨ Ù…Ù†",
        "month": "Ø´Ù‡Ø±",
        "table_housing": "Ø§Ù„Ø³ÙƒÙ†",
        "table_date": "Ø§Ù„ØªØ§Ø±ÙŠØ®",
        "table_amount": "Ø§Ù„Ù…Ø¨Ù„Øº",
        "table_payment": "Ø§Ù„Ø¯ÙØ¹",
        "table_reservation": "Ø§Ù„Ø­Ø¬Ø²",
        "table_actions": "Ø§Ù„Ø¥Ø¬Ø±Ø§Ø¡Ø§Øª",
        "pay": "Ø¯ÙØ¹",
        "review": "ØªÙ‚ÙŠÙŠÙ…",
        "no_reservation": "Ù„Ø§ ØªÙˆØ¬Ø¯ Ø­Ø¬ÙˆØ²Ø§Øª.",
        "messages_title": "Ù…Ø­Ø§Ø¯Ø«Ø§ØªÙŠ",
        "view_housing": "Ø¹Ø±Ø¶ Ø§Ù„Ø³ÙƒÙ†",
        "discussions": "Ø§Ù„Ù…Ø­Ø§Ø¯Ø«Ø§Øª",
        "no_discussion_title": "Ù„Ø§ ØªÙˆØ¬Ø¯ Ù…Ø­Ø§Ø¯Ø«Ø© Ø­Ø§Ù„ÙŠØ§",
        "no_discussion_text": "Ø³ØªØ¸Ù‡Ø± Ø§Ù„Ù…Ø­Ø§Ø¯Ø«Ø§Øª Ù‡Ù†Ø§ Ø¨Ø¹Ø¯ Ø¥Ø±Ø³Ø§Ù„ Ø£ÙˆÙ„ Ø±Ø³Ø§Ù„Ø© Ù…Ù† Ø¥Ø¹Ù„Ø§Ù†.",
        "chat_preview_text": "Ø§Ø®ØªØ± Ù…Ø­Ø§Ø¯Ø«Ø© Ù„Ø¹Ø±Ø¶ Ø§Ù„Ø±Ø³Ø§Ø¦Ù„ ÙˆØ§Ù„Ø±Ø¯ Ù…Ø«Ù„ ØªØ·Ø¨ÙŠÙ‚Ø§Øª Ø§Ù„Ù…Ø±Ø§Ø³Ù„Ø©.",
        "owner_label": "Ø§Ù„Ù…Ø§Ù„Ùƒ",
        "student_label": "Ø§Ù„Ø·Ø§Ù„Ø¨",
        "all_discussions": "ÙƒÙ„ Ø§Ù„Ù…Ø­Ø§Ø¯Ø«Ø§Øª",
        "conversation": "Ù…Ø­Ø§Ø¯Ø«Ø©",
        "back": "Ø±Ø¬ÙˆØ¹",
        "no_message_discussion": "Ù„Ø§ ØªÙˆØ¬Ø¯ Ø±Ø³Ø§Ø¦Ù„ ÙÙŠ Ù‡Ø°Ù‡ Ø§Ù„Ù…Ø­Ø§Ø¯Ø«Ø©.",
        "write_message": "Ø§ÙƒØªØ¨ Ø±Ø³Ø§Ù„Ø©...",
        "send": "Ø¥Ø±Ø³Ø§Ù„",
        "help_title": "Ù‡Ù„ ØªØ­ØªØ§Ø¬ Ù…Ø³Ø§Ø¹Ø¯Ø©ØŸ",
        "help_text": "Ø§ÙƒØªØ¨ Ø·Ù„Ø¨ Ù…Ø³Ø§Ø¹Ø¯Ø© Ø£Ùˆ Ù…Ù„Ø§Ø­Ø¸Ø© Ø£Ùˆ ØªØ¹Ù„ÙŠÙ‚Ø§. Ø³ÙŠØªÙ… Ø¥Ø¶Ø§ÙØ© Ø§Ø³Ù…Ùƒ ÙˆØ¨Ø±ÙŠØ¯Ùƒ ØªÙ„Ù‚Ø§Ø¦ÙŠØ§ Ù…Ù† Ø­Ø³Ø§Ø¨Ùƒ.",
        "name": "Ø§Ù„Ø§Ø³Ù…",
        "subject": "Ø§Ù„Ù…ÙˆØ¶ÙˆØ¹",
        "help_subject_placeholder": "Ù…Ø«Ø§Ù„: Ù…Ø´ÙƒÙ„Ø© ÙÙŠ Ø§Ù„Ø­Ø¬Ø²",
        "message_or_comment": "Ø±Ø³Ø§Ù„Ø© Ø£Ùˆ ØªØ¹Ù„ÙŠÙ‚",
        "help_message_placeholder": "ØµÙ Ø·Ù„Ø¨Ùƒ...",
        "send_request": "Ø¥Ø±Ø³Ø§Ù„ Ø§Ù„Ø·Ù„Ø¨",
    },
}

TRANSLATIONS["ar"].update({
    "nav_housing": "السكن",
    "nav_dashboard": "لوحة التحكم",
    "nav_reservations": "الحجوزات",
    "nav_messages": "الرسائل",
    "nav_help": "مساعدة",
    "nav_profile": "الملف الشخصي",
    "nav_add": "إضافة",
    "nav_admin": "الإدارة",
    "nav_logout": "خروج",
    "nav_login": "دخول",
    "nav_register": "تسجيل",
    "nav_home": "الرئيسية",
    "nav_favorites": "المفضلة",
    "nav_colocation": "السكن المشترك",
    "nav_vault": "الخزنة الرقمية",
    "budget_recommendation": "الميزانية المقترحة",
    "min_rooms": "أقل عدد غرف",
    "floor": "الطابق",
    "max_distance_faculty": "أقصى مسافة عن الكلية (كم)",
    "colocation_only": "السكن المشترك فقط",
    "interactive_map": "خريطة تفاعلية",
    "show_map": "إظهار الخريطة",
    "recommended_housing": "سكن مقترح لك",
    "contract": "عقد",
    "no_action": "لا إجراء",
    "university_year": "السنة الجامعية",
    "smoker": "مدخن",
    "budget": "الميزانية",
    "roommate_space": "فضاء السكن المشترك",
    "roommate_profile": "ملفي للسكن المشترك",
    "compatible_profiles": "ملفات متوافقة",
    "roommate_budget_calculator": "حاسبة ميزانية السكن المشترك",
    "footer": "StudentHome - منصة السكن الطلابي لجامعة القاضي عياض",
    "hero_tag": "سكن طلاب جامعة القاضي عياض",
    "hero_title": "اعثر على سكن قريب من كليتك.",
    "hero_text": "يساعد StudentHome الطلاب على البحث والحجز وتتبع الطلبات بسهولة.",
    "explore_housing": "استكشاف السكن",
    "create_account": "إنشاء حساب",
    "popular_housing": "إعلانات مميزة",
    "view_all": "عرض الكل",
    "no_listing_title": "لا توجد إعلانات حاليا",
    "no_listing_text": "ستظهر الإعلانات هنا عندما ينشر أول مالك إعلانه.",
    "create_owner_account": "إنشاء حساب مالك",
    "for_students": "للطلاب",
    "for_students_text": "البحث حسب الكلية والحي والسعر والحجز وتتبع الطلبات والتقييمات.",
    "for_owners": "للمالكين",
    "for_owners_text": "نشر الإعلانات، إدارة الطلبات وتأكيد مطابقة السكن.",
    "choose_role_title": "اختر نوع الحساب",
    "choose_role_text": "اختر الملف المناسب لاستخدامك لمنصة StudentHome.",
    "student": "طالب",
    "owner": "مالك",
    "student_choice_text": "ابحث عن السكن، تواصل مع المالكين وتابع حجوزاتك.",
    "owner_choice_text": "انشر إعلاناتك، أجب الطلاب وقم بإدارة الطلبات.",
    "continue": "متابعة",
    "register_title": "تسجيل",
    "login_title": "دخول",
    "full_name": "الاسم الكامل",
    "email": "البريد الإلكتروني",
    "password": "كلمة المرور",
    "faculty": "كلية UCA",
    "massar_code": "رمز مسار",
    "phone": "الهاتف",
    "create_the_account": "إنشاء الحساب",
    "identifier": "المعرّف",
    "login_button": "دخول",
    "login_continue_text": "سجل الدخول لمتابعة العملية.",
    "login_identifier_placeholder": "رمز مسار للطالب أو البريد الإلكتروني",
    "forgot_password": "نسيت كلمة المرور؟",
    "create_student_account": "إنشاء حساب طالب",
    "change": "تغيير",
    "register_continue_text": "أنشئ حسابك لمتابعة العملية على StudentHome.",
    "strong_password_placeholder": "8 أحرف، حرف كبير، حرف صغير، رقم، رمز خاص",
    "massar_example": "مثال: G123456789",
    "profile_title": "ملفي الشخصي",
    "profile_hint": "يبقى بريدك الإلكتروني مقفلا. يمكنك تعديل باقي معلومات حسابك.",
    "profile_photo": "صورة الملف الشخصي",
    "profile_photo_hint": "أضف صورة JPG أو PNG أو WEBP. إذا لم تختر شيئا فسيبقى الرمز الحالي.",
    "change_password": "تغيير كلمة المرور",
    "keep_password_hint": "اترك هذه الخانات فارغة إذا أردت الاحتفاظ بكلمة المرور الحالية.",
    "new_password": "كلمة مرور جديدة",
    "confirm_password": "تأكيد كلمة المرور",
    "password_min_placeholder": "8 أحرف على الأقل",
    "repeat_password_placeholder": "أعد كتابة كلمة المرور",
    "save_changes": "حفظ التعديلات",
    "search_housing_title": "البحث عن سكن",
    "search_placeholder": "اكتب بحثا: الحي، الكلية، العنوان...",
    "filter": "تصفية",
    "search": "بحث",
    "sector_marrakech": "الحي في مراكش",
    "all_sectors": "كل الأحياء",
    "min_price": "أقل سعر",
    "max_price": "أعلى سعر",
    "housing_type": "نوع السكن",
    "all_types": "كل الأنواع",
    "near_faculty": "الكلية القريبة",
    "available_only": "المتاح فقط",
    "reset": "إعادة ضبط",
    "apply_filters": "تطبيق الفلاتر",
    "no_listing_now": "لا توجد إعلانات حاليا",
    "no_listing_long": "لم يتم نشر أي سكن على StudentHome بعد. عندما يضيف مالك إعلانا سيظهر هنا.",
    "publish_first_listing": "نشر أول إعلان",
    "available_from": "متاح ابتداء من",
    "available": "متاح",
    "unavailable": "غير متاح",
    "view_details": "عرض التفاصيل",
    "close_to": "قريب من",
    "month": "شهر",
    "table_housing": "السكن",
    "table_date": "التاريخ",
    "table_amount": "المبلغ",
    "table_payment": "الدفع",
    "table_reservation": "الحجز",
    "table_actions": "الإجراءات",
    "pay": "دفع",
    "review": "تقييم",
    "no_reservation": "لا توجد حجوزات.",
    "messages_title": "محادثاتي",
    "view_housing": "عرض السكن",
    "discussions": "المحادثات",
    "no_discussion_title": "لا توجد محادثة حاليا",
    "no_discussion_text": "ستظهر المحادثات هنا بعد إرسال أول رسالة من إعلان.",
    "chat_preview_text": "اختر محادثة لعرض الرسائل والرد مثل تطبيقات المراسلة.",
    "owner_label": "المالك",
    "student_label": "الطالب",
    "all_discussions": "كل المحادثات",
    "conversation": "محادثة",
    "back": "رجوع",
    "no_message_discussion": "لا توجد رسائل في هذه المحادثة.",
    "write_message": "اكتب رسالة...",
    "send": "إرسال",
    "help_title": "هل تحتاج مساعدة؟",
    "help_text": "اكتب طلب مساعدة أو ملاحظة أو تعليقا. سيتم إضافة اسمك وبريدك الإلكتروني تلقائيا من حسابك.",
    "name": "الاسم",
    "subject": "الموضوع",
    "help_subject_placeholder": "مثال: مشكلة في الحجز",
    "message_or_comment": "رسالة أو تعليق",
    "help_message_placeholder": "صف طلبك...",
    "send_request": "إرسال الطلب",
})

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Connectez-vous pour continuer."
app.jinja_env.filters["fix_encoding"] = fix_text_encoding


class Utilisateur(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    photo_profil = db.Column(db.String(220), nullable=True)

    etudiant = db.relationship("Etudiant", backref="utilisateur", uselist=False, cascade="all, delete")
    proprietaire = db.relationship("Proprietaire", backref="utilisateur", uselist=False, cascade="all, delete")

    @property
    def avatar_path(self):
        if self.photo_profil:
            return self.photo_profil
        return None


class Etudiant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    faculte_uca = db.Column(db.String(120), nullable=False)
    numero_etudiant = db.Column(db.String(80), nullable=False)


class Proprietaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    telephone = db.Column(db.String(40), nullable=False)
    est_verifie = db.Column(db.Boolean, default=False)


class Logement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(160), nullable=False)
    adresse = db.Column(db.String(220), nullable=True)
    description = db.Column(db.Text, nullable=False)
    reglement_interieur = db.Column(db.Text, nullable=True)
    prix = db.Column(db.Float, nullable=False)
    quartier = db.Column(db.String(100), nullable=False)
    proximite_faculte = db.Column(db.String(120), nullable=False)
    type_logement = db.Column(db.String(80), default="Studio")
    nombre_chambres = db.Column(db.Integer, default=1)
    etage = db.Column(db.Integer, default=0)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    est_colocation = db.Column(db.Boolean, default=False)
    vues = db.Column(db.Integer, default=0)
    photos = db.Column(db.String(220), default="marrakech-rooftop-sunset.jpg")
    est_disponible = db.Column(db.Boolean, default=True)
    date_disponibilite = db.Column(db.String(20), nullable=True)
    est_valide = db.Column(db.Boolean, default=False)
    est_bloque = db.Column(db.Boolean, default=False)
    proprietaire_id = db.Column(db.Integer, db.ForeignKey("proprietaire.id"), nullable=False)

    proprietaire = db.relationship("Proprietaire", backref="logements")
    reservations = db.relationship("Reservation", backref="logement", cascade="all, delete")
    avis = db.relationship("Avis", backref="logement", cascade="all, delete")
    medias = db.relationship(
        "LogementMedia",
        backref="logement",
        cascade="all, delete-orphan",
        order_by="LogementMedia.ordre",
    )

    @property
    def raw_media_path(self):
        if self.photos and self.photos.startswith("uploads/"):
            return self.photos
        return "images/" + (self.photos or "marrakech-rooftop-sunset.jpg")

    @property
    def media_path(self):
        if self.visible_medias:
            return self.visible_medias[0].media_path
        if os.path.exists(os.path.join(BASE_DIR, "static", self.raw_media_path)):
            return self.raw_media_path
        return "images/marrakech-rooftop-sunset.jpg"

    @property
    def media_exists(self):
        return os.path.exists(os.path.join(BASE_DIR, "static", self.raw_media_path))

    @property
    def visible_medias(self):
        available_medias = [media for media in self.medias if media.media_exists]
        if available_medias:
            return available_medias
        return []

    @property
    def is_video(self):
        extension = self.media_path.rsplit(".", 1)[-1].lower()
        return extension in VIDEO_EXTENSIONS

    @property
    def availability_text(self):
        if not self.date_disponibilite:
            return ""
        try:
            available_date = date.fromisoformat(self.date_disponibilite)
        except ValueError:
            return "Disponible a partir du " + self.date_disponibilite
        if available_date <= date.today():
            return "Disponible dès le " + self.date_disponibilite
        return "Disponible a partir du " + self.date_disponibilite


class LogementMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    logement_id = db.Column(db.Integer, db.ForeignKey("logement.id"), nullable=False)
    fichier = db.Column(db.String(220), nullable=False)
    ordre = db.Column(db.Integer, default=0)

    @property
    def media_path(self):
        if self.fichier.startswith("uploads/"):
            return self.fichier
        return "images/" + self.fichier

    @property
    def media_exists(self):
        return os.path.exists(os.path.join(BASE_DIR, "static", self.media_path))

    @property
    def is_video(self):
        extension = self.fichier.rsplit(".", 1)[-1].lower()
        return extension in VIDEO_EXTENSIONS


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    logement_id = db.Column(db.Integer, db.ForeignKey("logement.id"), nullable=False)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("etudiant.id"), nullable=False)
    date_debut = db.Column(db.String(20), nullable=False)
    montant_total = db.Column(db.Float, nullable=False)
    statut_paiement = db.Column(db.String(40), default="Non payÃ©")
    statut_reservation = db.Column(db.String(60), default="En attente de validation")

    etudiant = db.relationship("Etudiant", backref="reservations")


class Avis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    logement_id = db.Column(db.Integer, db.ForeignKey("logement.id"), nullable=False)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("etudiant.id"), nullable=False)
    note = db.Column(db.Integer, nullable=False)
    commentaire = db.Column(db.Text, nullable=False)
    date_publication = db.Column(db.String(20), default=lambda: date.today().isoformat())
    est_visible = db.Column(db.Boolean, default=True)

    etudiant = db.relationship("Etudiant", backref="avis")


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    logement_id = db.Column(db.Integer, db.ForeignKey("logement.id"), nullable=False)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("etudiant.id"), nullable=False)
    proprietaire_id = db.Column(db.Integer, db.ForeignKey("proprietaire.id"), nullable=False)
    expediteur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    sujet = db.Column(db.String(160), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_envoi = db.Column(db.String(20), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    logement = db.relationship("Logement", backref="messages")
    etudiant = db.relationship("Etudiant", backref="messages")
    proprietaire = db.relationship("Proprietaire", backref="messages")
    expediteur = db.relationship("Utilisateur", backref="messages_envoyes")


class SupportMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    sujet = db.Column(db.String(160), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_envoi = db.Column(db.String(20), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=True)

    utilisateur = db.relationship("Utilisateur", backref="support_messages")


class Favori(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    logement_id = db.Column(db.Integer, db.ForeignKey("logement.id"), nullable=False)
    date_ajout = db.Column(db.String(20), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    utilisateur = db.relationship("Utilisateur", backref="favoris")
    logement = db.relationship("Logement", backref="favoris")


class ProfilColocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("etudiant.id"), nullable=False)
    budget = db.Column(db.Float, default=0)
    faculte = db.Column(db.String(120), nullable=False)
    fumeur = db.Column(db.String(20), default="non")
    sommeil = db.Column(db.String(40), default="normal")
    proprete = db.Column(db.String(40), default="normal")
    serieux = db.Column(db.String(40), default="normal")
    langue = db.Column(db.String(40), default="francais")
    annee_universitaire = db.Column(db.Integer, default=1)

    etudiant = db.relationship("Etudiant", backref="profil_colocation", uselist=False)


class Visite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    logement_id = db.Column(db.Integer, db.ForeignKey("logement.id"), nullable=False)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("etudiant.id"), nullable=False)
    proprietaire_id = db.Column(db.Integer, db.ForeignKey("proprietaire.id"), nullable=False)
    date_visite = db.Column(db.String(20), nullable=False)
    statut = db.Column(db.String(40), default="En attente")

    logement = db.relationship("Logement", backref="visites")
    etudiant = db.relationship("Etudiant", backref="visites")
    proprietaire = db.relationship("Proprietaire", backref="visites")


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    type_document = db.Column(db.String(80), nullable=False)
    fichier = db.Column(db.String(220), nullable=False)
    date_upload = db.Column(db.String(20), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    utilisateur = db.relationship("Utilisateur", backref="documents")


class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    logement_id = db.Column(db.Integer, db.ForeignKey("logement.id"), nullable=False)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("etudiant.id"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String(220), nullable=True)
    statut = db.Column(db.String(40), default="Signale")
    date_signalement = db.Column(db.String(20), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    logement = db.relationship("Logement", backref="incidents")
    etudiant = db.relationship("Etudiant", backref="incidents")


class InventaireItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    logement_id = db.Column(db.Integer, db.ForeignKey("logement.id"), nullable=False)
    nom = db.Column(db.String(120), nullable=False)
    categorie = db.Column(db.String(80), default="Equipement")
    etat_declare = db.Column(db.String(80), default="Bon etat")
    etat_valide = db.Column(db.String(80), nullable=True)
    commentaire_etudiant = db.Column(db.Text, nullable=True)
    est_valide = db.Column(db.Boolean, default=False)
    date_validation = db.Column(db.String(20), nullable=True)

    logement = db.relationship("Logement", backref="inventaire")


@login_manager.user_loader
def load_user(user_id):
    return Utilisateur.query.get(int(user_id))


@app.context_processor
def inject_language_helpers():
    lang = session.get("lang", "fr")
    if lang not in SUPPORTED_LANGUAGES:
        lang = "fr"

    def t(key):
        value = TRANSLATIONS.get(lang, TRANSLATIONS["fr"]).get(key, TRANSLATIONS["fr"].get(key, key))
        return fix_text_encoding(value)

    return {"t": t, "current_lang": lang, "is_rtl": lang == "ar"}


def is_valid_massar(code_massar):
    # Format simple du code Massar marocain : une lettre suivie de 9 chiffres.
    return bool(re.fullmatch(r"[A-Z][0-9]{9}", code_massar.strip().upper()))


def is_valid_email(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip().lower()))


def password_errors(password):
    # RÃ¨gles lisibles pour Ã©viter les mots de passe trop faibles.
    errors = []
    if len(password) < 8:
        errors.append("au moins 8 caracteres")
    if not re.search(r"[A-Z]", password):
        errors.append("une lettre majuscule")
    if not re.search(r"[a-z]", password):
        errors.append("une lettre minuscule")
    if not re.search(r"[0-9]", password):
        errors.append("un chiffre")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("un caractere special")
    return errors


def safe_next_url(default_endpoint="index"):
    # On accepte seulement les redirections internes pour eviter les liens externes dangereux.
    next_url = request.form.get("next") or request.args.get("next")
    if next_url and next_url.startswith("/"):
        return next_url
    return url_for(default_endpoint)


def is_allowed_media(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_MEDIA_EXTENSIONS


def save_uploaded_media(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not is_allowed_media(file_storage.filename):
        return None

    filename = secure_filename(file_storage.filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    saved_name = f"{timestamp}_{filename}"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_storage.save(os.path.join(UPLOAD_FOLDER, saved_name))
    return "uploads/" + saved_name


def save_uploaded_media_list(file_list, limit=MAX_ANNONCE_MEDIA):
    files = [file for file in file_list if file and file.filename]
    if len(files) > limit:
        return [], f"Vous pouvez ajouter {limit} fichiers maximum par annonce."

    saved_files = []
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    for index, file_storage in enumerate(files, start=1):
        if not is_allowed_media(file_storage.filename):
            return [], "Format media non autorise. Utilisez jpg, png, webp, mp4, webm ou mov."

        filename = secure_filename(file_storage.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        saved_name = f"{timestamp}_{index}_{filename}"
        file_storage.save(os.path.join(UPLOAD_FOLDER, saved_name))
        saved_files.append("uploads/" + saved_name)

    return saved_files, None


def save_uploaded_profile_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    extension = file_storage.filename.rsplit(".", 1)[-1].lower()
    if "." not in file_storage.filename or extension not in PROFILE_IMAGE_EXTENSIONS:
        return None

    filename = secure_filename(file_storage.filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    saved_name = f"profile_{timestamp}_{filename}"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_storage.save(os.path.join(UPLOAD_FOLDER, saved_name))
    return "uploads/" + saved_name


def save_uploaded_document(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    filename = secure_filename(file_storage.filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    saved_name = f"doc_{timestamp}_{filename}"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_storage.save(os.path.join(UPLOAD_FOLDER, saved_name))
    return "uploads/" + saved_name


def haversine_km(lat1, lng1, lat2, lng2):
    radius = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return round(radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


def guess_coordinates(quartier):
    return QUARTIER_COORDS.get(quartier, (31.6295, -7.9811))


def distance_to_faculty(logement, faculte_code):
    faculte = FACULTES_UCA.get(faculte_code)
    if not faculte or logement.latitude is None or logement.longitude is None:
        return None
    return haversine_km(logement.latitude, logement.longitude, faculte["lat"], faculte["lng"])


def recommendation_score(logement, budget=None, faculte_code=None, type_pref="", colocation=False):
    score = 0
    if budget:
        ecart_budget = abs(logement.prix - budget)
        if logement.prix <= budget:
            score += max(0, 45 - int(ecart_budget / 100))
        else:
            score += max(0, 20 - int((logement.prix - budget) / 100))
    if type_pref and logement.type_logement == type_pref:
        score += 20
    if colocation and logement.est_colocation:
        score += 15
    distance = distance_to_faculty(logement, faculte_code) if faculte_code else None
    if distance is not None:
        score += max(0, 45 - int(distance * 10))
    return score


def description_has_max_30_lines(description):
    return len(description.splitlines()) <= 30


def role_required(role):
    # Petit dÃ©corateur pour protÃ©ger les pages selon le rÃ´le connectÃ©.
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash("AccÃ¨s rÃ©servÃ©.", "error")
                return redirect(url_for("index"))
            return function(*args, **kwargs)

        return wrapper

    return decorator


def seed_database():
    # Pas de comptes de demonstration : les statistiques doivent refleter les vrais inscrits.
    return


def update_demo_student_account():
    # Met a jour le compte etudiant de demonstration si database.db existe deja.
    user = Utilisateur.query.filter_by(email="sara@uca.ac.ma").first()
    if not user or not user.etudiant:
        return

    changed = False
    if user.etudiant.numero_etudiant != "G123456789":
        user.etudiant.numero_etudiant = "G123456789"
        changed = True
    if not check_password_hash(user.mot_de_passe, "Etudiant@123"):
        user.mot_de_passe = generate_password_hash("Etudiant@123")
        changed = True
    if changed:
        db.session.commit()


def remove_demo_housing():
    # L'application doit commencer sans annonces : elles seront ajoutees par les proprietaires.
    demo_titles = [
        "Studio lumineux prÃ¨s de la FSSM",
        "Chambre calme pour Ã©tudiante",
        "Appartement Ã©conomique",
    ]
    deleted = False
    for title in demo_titles:
        logement = Logement.query.filter_by(titre=title).first()
        if logement:
            db.session.delete(logement)
            deleted = True
    if deleted:
        db.session.commit()


def delete_logement_tree(logement):
    Favori.query.filter_by(logement_id=logement.id).delete()
    Message.query.filter_by(logement_id=logement.id).delete()
    Visite.query.filter_by(logement_id=logement.id).delete()
    Incident.query.filter_by(logement_id=logement.id).delete()
    InventaireItem.query.filter_by(logement_id=logement.id).delete()
    Avis.query.filter_by(logement_id=logement.id).delete()
    Reservation.query.filter_by(logement_id=logement.id).delete()
    db.session.delete(logement)


def remove_demo_users():
    demo_users = Utilisateur.query.filter(
        Utilisateur.email.in_(["sara@uca.ac.ma", "youssef@mail.com"])
    ).all()
    changed = False
    for user in demo_users:
        if user.proprietaire:
            for logement in list(user.proprietaire.logements):
                delete_logement_tree(logement)
            Message.query.filter_by(proprietaire_id=user.proprietaire.id).delete()
            Visite.query.filter_by(proprietaire_id=user.proprietaire.id).delete()
            db.session.delete(user.proprietaire)
            changed = True
        if user.etudiant:
            etudiant_id = user.etudiant.id
            Favori.query.filter_by(utilisateur_id=user.id).delete()
            Message.query.filter_by(etudiant_id=etudiant_id).delete()
            Message.query.filter_by(expediteur_id=user.id).delete()
            Visite.query.filter_by(etudiant_id=etudiant_id).delete()
            Incident.query.filter_by(etudiant_id=etudiant_id).delete()
            Avis.query.filter_by(etudiant_id=etudiant_id).delete()
            Reservation.query.filter_by(etudiant_id=etudiant_id).delete()
            profil = ProfilColocation.query.filter_by(etudiant_id=etudiant_id).first()
            if profil:
                db.session.delete(profil)
            db.session.delete(user.etudiant)
            changed = True
        db.session.delete(user)
        changed = True
    if changed:
        db.session.commit()


def sync_admin_account():
    # Un seul compte a le droit d'avoir le role administrateur.
    admins = Utilisateur.query.filter_by(role="admin").all()
    for admin in admins:
        if admin.email != ADMIN_EMAIL:
            db.session.delete(admin)

    admin_user = Utilisateur.query.filter_by(email=ADMIN_EMAIL).first()
    if admin_user:
        admin_user.role = "admin"
    else:
        admin_user = Utilisateur(
            nom="Administrateur StudentHome",
            email=ADMIN_EMAIL,
            mot_de_passe=generate_password_hash(ADMIN_DEFAULT_PASSWORD),
            role="admin",
        )
        db.session.add(admin_user)
    db.session.commit()


def ensure_non_admin_roles():
    # Si un utilisateur emploie l'email admin dans un autre role, on nettoie son profil secondaire.
    admin_user = Utilisateur.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin_user:
        return
    changed = False
    if admin_user.etudiant:
        db.session.delete(admin_user.etudiant)
        changed = True
    if admin_user.proprietaire:
        db.session.delete(admin_user.proprietaire)
        changed = True
    if changed:
        db.session.commit()


def is_sqlite_database():
    return db.engine.url.get_backend_name() == "sqlite"


def ensure_user_profile_photo_column():
    columns = db.session.execute(text("PRAGMA table_info(utilisateur)")).fetchall()
    column_names = [column[1] for column in columns]
    if "photo_profil" not in column_names:
        db.session.execute(text("ALTER TABLE utilisateur ADD COLUMN photo_profil VARCHAR(220)"))
        db.session.commit()


def ensure_logement_advanced_columns():
    columns = db.session.execute(text("PRAGMA table_info(logement)")).fetchall()
    column_names = [column[1] for column in columns]
    advanced_columns = {
        "adresse": "VARCHAR(220)",
        "reglement_interieur": "TEXT",
        "nombre_chambres": "INTEGER DEFAULT 1",
        "etage": "INTEGER DEFAULT 0",
        "latitude": "FLOAT",
        "longitude": "FLOAT",
        "est_colocation": "BOOLEAN DEFAULT 0",
        "vues": "INTEGER DEFAULT 0",
    }
    for column_name, column_type in advanced_columns.items():
        if column_name not in column_names:
            db.session.execute(text(f"ALTER TABLE logement ADD COLUMN {column_name} {column_type}"))
    db.session.commit()


def ensure_colocation_year_column():
    columns = db.session.execute(text("PRAGMA table_info(profil_colocation)")).fetchall()
    column_names = [column[1] for column in columns]
    if "annee_universitaire" not in column_names:
        db.session.execute(text("ALTER TABLE profil_colocation ADD COLUMN annee_universitaire INTEGER DEFAULT 1"))
        db.session.commit()


def init_database():
    # La base est crÃ©Ã©e automatiquement au lancement.
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    db.create_all()
    if is_sqlite_database():
        ensure_user_profile_photo_column()
        ensure_logement_advanced_columns()
        ensure_colocation_year_column()
        ensure_logement_type_column()
        ensure_logement_availability_date_column()
    seed_database()
    remove_demo_housing()
    remove_demo_users()
    sync_admin_account()
    ensure_non_admin_roles()


def ensure_logement_type_column():
    # SQLite ne modifie pas automatiquement les tables deja creees par db.create_all().
    columns = db.session.execute(text("PRAGMA table_info(logement)")).fetchall()
    column_names = [column[1] for column in columns]
    if "type_logement" not in column_names:
        db.session.execute(text("ALTER TABLE logement ADD COLUMN type_logement VARCHAR(80) DEFAULT 'Studio'"))
        db.session.commit()


def ensure_logement_availability_date_column():
    columns = db.session.execute(text("PRAGMA table_info(logement)")).fetchall()
    column_names = [column[1] for column in columns]
    if "date_disponibilite" not in column_names:
        db.session.execute(text("ALTER TABLE logement ADD COLUMN date_disponibilite VARCHAR(20)"))
        db.session.commit()


@app.route("/")
def index():
    logements = (
        Logement.query.filter_by(est_valide=True, est_bloque=False)
        .order_by(Logement.vues.desc(), Logement.id.desc())
        .limit(3)
        .all()
    )
    return render_template("index.html", logements=logements)


@app.route("/studenthome-marrakech")
def studenthome_marrakech():
    return index()


@app.route("/lang/<lang_code>")
def set_language(lang_code):
    if lang_code in SUPPORTED_LANGUAGES:
        session["lang"] = lang_code
    next_url = request.referrer
    if next_url and next_url.startswith(request.host_url):
        return redirect(next_url)
    return redirect(url_for("index"))


@app.route("/choisir-role")
def choisir_role():
    return render_template("choisir_role.html", next_url=request.args.get("next", ""))


@app.route("/aide", methods=["GET", "POST"])
@login_required
def aide():
    if request.method == "POST":
        sujet = request.form["sujet"].strip()
        contenu = request.form["contenu"].strip()

        if not sujet or not contenu:
            flash("Veuillez remplir tous les champs d'aide.", "error")
            return redirect(url_for("aide"))

        support_message = SupportMessage(
            nom=current_user.nom,
            email=current_user.email,
            sujet=sujet,
            contenu=contenu,
            utilisateur_id=current_user.id,
        )
        db.session.add(support_message)
        db.session.commit()
        flash("Votre message d'aide a Ã©tÃ© envoyÃ© Ã  l'administrateur.", "success")
        return redirect(url_for("aide"))

    return render_template("aide.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            app.logger.info("REGISTER STEP 1: received form")
            nom = request.form.get("nom", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("mot_de_passe", "")
            role = request.form.get("role", "etudiant").strip()
            next_url = request.form.get("next", "")

            if email == ADMIN_EMAIL:
                role = "admin"
            if role not in ["etudiant", "proprietaire", "admin"]:
                role = "etudiant"

            if not nom or not email or not password:
                flash("Veuillez remplir tous les champs obligatoires.", "error")
                return redirect(url_for("register", role=role, next=next_url))
            if not is_valid_email(email):
                flash("Adresse email invalide.", "error")
                return redirect(url_for("register", role=role, next=next_url))

            errors = password_errors(password)
            if errors:
                flash("Mot de passe trop faible. Il doit contenir : " + ", ".join(errors) + ".", "error")
                return redirect(url_for("register", role=role, next=next_url))

            numero = request.form.get("numero_etudiant", "").strip().upper()
            faculte = request.form.get("faculte_uca", "").strip()
            telephone = request.form.get("telephone", "").strip()

            if role == "etudiant":
                if not faculte or not numero:
                    flash("La faculte et le code Massar sont obligatoires.", "error")
                    return redirect(url_for("register", role=role, next=next_url))
                if not is_valid_massar(numero):
                    flash("Code Massar invalide. Exemple attendu : G123456789.", "error")
                    return redirect(url_for("register", role=role, next=next_url))
            elif role == "proprietaire" and not telephone:
                flash("Le numero de telephone est obligatoire.", "error")
                return redirect(url_for("register", role=role, next=next_url))

            app.logger.info("REGISTER STEP 2: validation ok")
            app.logger.info("REGISTER STEP 3: checking existing email")
            if Utilisateur.query.filter_by(email=email).first():
                flash("Cet email est deja utilise.", "error")
                return redirect(url_for("register", role=role, next=next_url))
            if role == "etudiant" and Etudiant.query.filter_by(numero_etudiant=numero).first():
                flash("Ce code Massar est deja utilise.", "error")
                return redirect(url_for("register", role=role, next=next_url))

            app.logger.info("REGISTER STEP 4: hashing password")
            password_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

            app.logger.info("REGISTER STEP 5: saving user")
            utilisateur = Utilisateur(
                nom=nom,
                email=email,
                mot_de_passe=password_hash,
                role=role,
            )
            db.session.add(utilisateur)
            db.session.flush()

            if role == "etudiant":
                db.session.add(
                    Etudiant(
                        utilisateur_id=utilisateur.id,
                        faculte_uca=faculte,
                        numero_etudiant=numero,
                    )
                )
            elif role == "proprietaire":
                db.session.add(
                    Proprietaire(
                        utilisateur_id=utilisateur.id,
                        telephone=telephone,
                        est_verifie=True,
                    )
                )

            db.session.commit()
            login_user(utilisateur)
            app.logger.info("REGISTER STEP 6: redirecting")
            flash("Compte cree avec succes. Vous etes maintenant connecte.", "success")
            if next_url and not next_url.startswith("/login") and not next_url.startswith("/register"):
                return redirect(next_url)
            if utilisateur.role == "etudiant":
                return redirect(url_for("dashboard_etudiant"))
            if utilisateur.role == "proprietaire":
                return redirect(url_for("dashboard_proprietaire"))
            if utilisateur.role == "admin":
                return redirect(url_for("dashboard_admin"))
            return redirect(url_for("index"))
        except Exception as exc:
            db.session.rollback()
            app.logger.exception("Erreur POST /register: %s", exc)
            flash("Impossible de creer le compte pour le moment. Reessayez dans quelques instants.", "error")
            return redirect(url_for("register", role=request.form.get("role", "etudiant"), next=request.form.get("next", "")))

    selected_role = request.args.get("role", "etudiant")
    if selected_role not in ["etudiant", "proprietaire"]:
        selected_role = "etudiant"
    return render_template("register.html", next_url=request.args.get("next", ""), selected_role=selected_role)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifiant = request.form["identifiant"].strip()
        password = request.form.get("mot_de_passe", "")
        utilisateur = None

        if "@" in identifiant:
            utilisateur = Utilisateur.query.filter_by(email=identifiant.lower()).first()
        else:
            etudiant = Etudiant.query.filter_by(numero_etudiant=identifiant.upper()).first()
            if etudiant:
                utilisateur = etudiant.utilisateur

        admin_without_password = identifiant.lower() == ADMIN_EMAIL and utilisateur and utilisateur.role == "admin"

        if utilisateur and (admin_without_password or check_password_hash(utilisateur.mot_de_passe, password)):
            login_user(utilisateur)
            if request.form.get("next"):
                return redirect(safe_next_url("index"))
            if utilisateur.role == "etudiant":
                return redirect(url_for("dashboard_etudiant"))
            if utilisateur.role == "proprietaire":
                return redirect(url_for("dashboard_proprietaire"))
            if utilisateur.role == "admin":
                return redirect(url_for("dashboard_admin"))
            flash("Ce rÃ´le n'est plus pris en charge.", "error")
            logout_user()
            return redirect(url_for("index"))

        flash("Identifiant ou mot de passe incorrect.", "error")

    return render_template("login.html", next_url=request.args.get("next", ""))


@app.route("/mot-de-passe-oublie", methods=["GET", "POST"])
def mot_de_passe_oublie():
    if request.method == "POST":
        flash("La reinitialisation par email/SMS est temporairement desactivee. Contactez l'administrateur pour changer votre mot de passe.", "error")
        return redirect(url_for("login"))

    return render_template("mot_de_passe_oublie.html")


@app.route("/reinitialiser-mot-de-passe", methods=["GET", "POST"])
def reinitialiser_mot_de_passe():
    flash("La reinitialisation par code est temporairement desactivee.", "error")
    return redirect(url_for("login"))


@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        nouveau_mot_de_passe = request.form.get("nouveau_mot_de_passe", "")
        confirmation = request.form.get("confirmation", "")
        photo = request.files.get("photo_profil")

        if not nom:
            flash("Le nom ne peut pas etre vide.", "error")
            return redirect(url_for("profil"))

        current_user.nom = nom

        if photo and photo.filename:
            saved_photo = save_uploaded_profile_image(photo)
            if not saved_photo:
                flash("Photo de profil invalide. Utilisez JPG, PNG ou WEBP.", "error")
                return redirect(url_for("profil"))
            current_user.photo_profil = saved_photo

        if current_user.role == "etudiant" and current_user.etudiant:
            faculte = request.form.get("faculte_uca", "").strip()
            numero = request.form.get("numero_etudiant", "").strip().upper()

            if not faculte:
                flash("La faculte UCA est obligatoire.", "error")
                return redirect(url_for("profil"))
            if not is_valid_massar(numero):
                flash("Code Massar invalide. Exemple attendu : G123456789.", "error")
                return redirect(url_for("profil"))

            existing_student = Etudiant.query.filter_by(numero_etudiant=numero).first()
            if existing_student and existing_student.id != current_user.etudiant.id:
                flash("Ce code Massar est deja utilise.", "error")
                return redirect(url_for("profil"))

            current_user.etudiant.faculte_uca = faculte
            current_user.etudiant.numero_etudiant = numero

        if current_user.role == "proprietaire" and current_user.proprietaire:
            telephone = request.form.get("telephone", "").strip()
            if not telephone:
                flash("Le numero de telephone est obligatoire.", "error")
                return redirect(url_for("profil"))
            current_user.proprietaire.telephone = telephone

        if nouveau_mot_de_passe or confirmation:
            if nouveau_mot_de_passe != confirmation:
                flash("Les deux mots de passe ne correspondent pas.", "error")
                return redirect(url_for("profil"))

            errors = password_errors(nouveau_mot_de_passe)
            if errors:
                flash("Mot de passe trop faible. Il doit contenir : " + ", ".join(errors) + ".", "error")
                return redirect(url_for("profil"))

            current_user.mot_de_passe = generate_password_hash(nouveau_mot_de_passe)

        db.session.commit()
        flash("Profil mis a jour avec succes.", "success")
        return redirect(url_for("profil"))

    return render_template("profil.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("DÃ©connexion rÃ©ussie.", "success")
    return redirect(url_for("index"))


@app.route("/logements")
def logements():
    query = Logement.query.filter_by(est_valide=True, est_bloque=False)
    recherche = request.args.get("recherche", "").strip()
    faculte = request.args.get("faculte", "").strip()
    quartier = request.args.get("quartier", "").strip()
    prix_min = request.args.get("prix_min", "").strip()
    prix_max = request.args.get("prix_max", "").strip()
    type_logement = request.args.get("type_logement", "").strip()
    chambres = request.args.get("chambres", "").strip()
    etage = request.args.get("etage", "").strip()
    distance_max = request.args.get("distance_max", "").strip()
    budget = request.args.get("budget", "").strip()
    colocation = request.args.get("colocation", "")
    disponible = request.args.get("disponible", "")

    if recherche:
        search_pattern = f"%{recherche}%"
        query = query.filter(
            or_(
                Logement.titre.ilike(search_pattern),
                Logement.description.ilike(search_pattern),
                Logement.quartier.ilike(search_pattern),
                Logement.proximite_faculte.ilike(search_pattern),
            )
        )
    if faculte:
        query = query.filter(Logement.proximite_faculte.ilike(f"%{faculte}%"))
    if quartier:
        query = query.filter(Logement.quartier.ilike(f"%{quartier}%"))
    if prix_min:
        query = query.filter(Logement.prix >= float(prix_min))
    if prix_max:
        query = query.filter(Logement.prix <= float(prix_max))
    if type_logement:
        query = query.filter(Logement.type_logement == type_logement)
    if chambres:
        query = query.filter(Logement.nombre_chambres >= int(chambres))
    if etage:
        query = query.filter(Logement.etage == int(etage))
    if colocation == "1":
        query = query.filter_by(est_colocation=True)
    if disponible == "1":
        query = query.filter_by(est_disponible=True)

    secteurs = [
        "Semlalia",
        "Daoudiate",
        "Gueliz",
        "M'Hamid",
        "Massira",
        "Sidi Abbad",
        "Amerchich",
        "Bab Doukkala",
        "Hivernage",
        "Medina",
        "Route de Safi",
        "Route de Casablanca",
        "Targa",
    ]
    types_logement = ["Studio", "Chambre", "Appartement", "Colocation", "Maison", "Residence etudiante"]
    logements_liste = query.all()
    distances = {}
    if faculte in FACULTES_UCA:
        for logement in logements_liste:
            distances[logement.id] = distance_to_faculty(logement, faculte)
        if distance_max:
            max_value = float(distance_max)
            logements_liste = [
                logement for logement in logements_liste
                if distances.get(logement.id) is not None and distances[logement.id] <= max_value
            ]

    budget_value = float(budget) if budget else (float(prix_max) if prix_max else None)
    reco_faculte = faculte
    if current_user.is_authenticated and current_user.role == "etudiant":
        reco_faculte = faculte or current_user.etudiant.faculte_uca
        if budget_value is None and current_user.etudiant.profil_colocation:
            budget_value = current_user.etudiant.profil_colocation.budget or None

    recommandations_source = Logement.query.filter_by(est_valide=True, est_bloque=False).all()
    recommandations = []
    if budget_value or reco_faculte:
        recommandations = sorted(
            recommandations_source,
            key=lambda logement: recommendation_score(logement, budget_value, reco_faculte, type_logement, colocation == "1"),
            reverse=True,
        )[:3]
    favoris_ids = set()
    if current_user.is_authenticated:
        favoris_ids = {favori.logement_id for favori in Favori.query.filter_by(utilisateur_id=current_user.id).all()}
    map_logements = [
        {
            "id": logement.id,
            "titre": logement.titre,
            "quartier": logement.quartier,
            "prix": int(logement.prix),
            "lat": logement.latitude,
            "lng": logement.longitude,
            "url": url_for("detail_logement", id=logement.id),
        }
        for logement in logements_liste
        if logement.latitude is not None and logement.longitude is not None
    ]
    return render_template(
        "logements.html",
        logements=logements_liste,
        recommandations=recommandations,
        favoris_ids=favoris_ids,
        map_logements=map_logements,
        map_facultes=FACULTES_UCA,
        distances=distances,
        secteurs=secteurs,
        types_logement=types_logement,
        facultes=FACULTES_UCA,
        filtres=request.args,
    )


@app.route("/logement/<int:id>", methods=["GET", "POST"])
def detail_logement(id):
    logement = Logement.query.get_or_404(id)
    logement.vues = (logement.vues or 0) + 1
    db.session.commit()
    if request.method == "POST":
        if not current_user.is_authenticated or current_user.role != "etudiant":
            flash("Connectez-vous avec un compte Ã©tudiant pour rÃ©server.", "error")
            return redirect(url_for("login", next=request.path))
        reservation = Reservation(
            logement_id=logement.id,
            etudiant_id=current_user.etudiant.id,
            date_debut=request.form["date_debut"],
            montant_total=logement.prix,
        )
        db.session.add(reservation)
        db.session.commit()
        flash("Demande de rÃ©servation envoyÃ©e au propriÃ©taire.", "success")
        return redirect(url_for("reservations"))
    favori_actif = False
    if current_user.is_authenticated and current_user.role == "etudiant":
        favori_actif = Favori.query.filter_by(utilisateur_id=current_user.id, logement_id=logement.id).first() is not None
    return render_template("detail_logement.html", logement=logement, favori_actif=favori_actif)


@app.route("/contacter-proprietaire/<int:id>", methods=["POST"])
def contacter_proprietaire(id):
    logement = Logement.query.get_or_404(id)
    if not current_user.is_authenticated or current_user.role != "etudiant":
        flash("Pour envoyer un message au propriÃ©taire, connectez-vous ou crÃ©ez un compte Ã©tudiant avec votre code Massar.", "error")
        return redirect(url_for("login", next=url_for("detail_logement", id=logement.id)))

    sujet = request.form.get("sujet", "").strip()
    message = request.form.get("message", "").strip()
    if not sujet or not message:
        flash("Veuillez saisir un sujet et un message.", "error")
        return redirect(url_for("detail_logement", id=logement.id))

    message_client = Message(
        logement_id=logement.id,
        etudiant_id=current_user.etudiant.id,
        proprietaire_id=logement.proprietaire_id,
        expediteur_id=current_user.id,
        sujet=sujet,
        contenu=message,
    )
    db.session.add(message_client)
    db.session.commit()
    flash("Votre message a Ã©tÃ© envoyÃ© au propriÃ©taire.", "success")
    return redirect(url_for("discussion", logement_id=logement.id, etudiant_id=current_user.etudiant.id))


@app.route("/favori/<int:id>")
@login_required
@role_required("etudiant")
def toggle_favori(id):
    logement = Logement.query.get_or_404(id)
    favori = Favori.query.filter_by(utilisateur_id=current_user.id, logement_id=logement.id).first()
    if favori:
        db.session.delete(favori)
        active = False
    else:
        db.session.add(Favori(utilisateur_id=current_user.id, logement_id=logement.id))
        active = True
    db.session.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        count = Favori.query.filter_by(logement_id=logement.id).count()
        return jsonify({"active": active, "count": count})

    flash("Annonce ajoutee aux favoris." if active else "Annonce retiree des favoris.", "success")
    return redirect(request.referrer or url_for("logements"))


@app.route("/favoris")
@login_required
@role_required("etudiant")
def favoris():
    favoris_user = Favori.query.filter_by(utilisateur_id=current_user.id).order_by(Favori.id.desc()).all()
    favoris_ids = {favori.logement_id for favori in favoris_user}
    return render_template("favoris.html", favoris=favoris_user, favoris_ids=favoris_ids)


@app.route("/planifier-visite/<int:id>", methods=["POST"])
@login_required
@role_required("etudiant")
def planifier_visite(id):
    logement = Logement.query.get_or_404(id)
    date_visite = request.form.get("date_visite", "")
    if not date_visite:
        flash("Choisissez une date de visite.", "error")
        return redirect(url_for("detail_logement", id=id))
    db.session.add(
        Visite(
            logement_id=logement.id,
            etudiant_id=current_user.etudiant.id,
            proprietaire_id=logement.proprietaire_id,
            date_visite=date_visite,
        )
    )
    db.session.commit()
    flash("Demande de visite envoyee au proprietaire.", "success")
    return redirect(url_for("detail_logement", id=id))


@app.route("/incident/<int:id>", methods=["POST"])
@login_required
@role_required("etudiant")
def signaler_incident(id):
    logement = Logement.query.get_or_404(id)
    description = request.form.get("description", "").strip()
    if not description:
        flash("Veuillez decrire l'incident.", "error")
        return redirect(url_for("detail_logement", id=id))
    photo = save_uploaded_media(request.files.get("photo_incident"))
    db.session.add(
        Incident(
            logement_id=logement.id,
            etudiant_id=current_user.etudiant.id,
            description=description,
            photo=photo,
        )
    )
    db.session.commit()
    flash("Incident signale au proprietaire.", "success")
    return redirect(url_for("detail_logement", id=id))


@app.route("/inventaire/<int:id>", methods=["GET", "POST"])
@login_required
def inventaire(id):
    logement = Logement.query.get_or_404(id)
    is_owner = current_user.role == "proprietaire" and logement.proprietaire_id == current_user.proprietaire.id
    is_student = current_user.role == "etudiant"

    if not is_owner and not is_student:
        flash("Inventaire inaccessible pour ce compte.", "error")
        return redirect(url_for("detail_logement", id=id))

    if request.method == "POST" and is_owner:
        nom = request.form.get("nom", "").strip()
        if not nom:
            flash("Ajoutez le nom de l'equipement.", "error")
            return redirect(url_for("inventaire", id=id))
        db.session.add(
            InventaireItem(
                logement_id=logement.id,
                nom=nom,
                categorie=request.form.get("categorie", "Equipement").strip(),
                etat_declare=request.form.get("etat_declare", "Bon etat").strip(),
            )
        )
        db.session.commit()
        flash("Element ajoute a l'inventaire.", "success")
        return redirect(url_for("inventaire", id=id))

    if request.method == "POST" and is_student:
        for item in logement.inventaire:
            item.etat_valide = request.form.get(f"etat_{item.id}", item.etat_declare)
            item.commentaire_etudiant = request.form.get(f"commentaire_{item.id}", "").strip()
            item.est_valide = request.form.get(f"valide_{item.id}") == "1"
            item.date_validation = datetime.now().strftime("%Y-%m-%d %H:%M")
        db.session.commit()
        flash("Inventaire valide. Les etats sont enregistres pour eviter les litiges.", "success")
        return redirect(url_for("inventaire", id=id))

    return render_template("inventaire.html", logement=logement, is_owner=is_owner, is_student=is_student)


@app.route("/inventaire/supprimer/<int:item_id>")
@login_required
@role_required("proprietaire")
def supprimer_inventaire_item(item_id):
    item = InventaireItem.query.get_or_404(item_id)
    logement_id = item.logement_id
    if item.logement.proprietaire_id != current_user.proprietaire.id:
        flash("Element inaccessible.", "error")
        return redirect(url_for("dashboard_proprietaire"))
    db.session.delete(item)
    db.session.commit()
    flash("Element retire de l'inventaire.", "success")
    return redirect(url_for("inventaire", id=logement_id))


@app.route("/messages")
@login_required
def messages():
    if current_user.role == "etudiant":
        messages_user = (
            Message.query.filter_by(etudiant_id=current_user.etudiant.id)
            .order_by(Message.id.desc())
            .all()
        )
    elif current_user.role == "proprietaire":
        messages_user = (
            Message.query.filter_by(proprietaire_id=current_user.proprietaire.id)
            .order_by(Message.id.desc())
            .all()
        )
    else:
        flash("La messagerie est rÃ©servÃ©e aux Ã©tudiants et propriÃ©taires.", "error")
        return redirect(url_for("index"))

    discussions = []
    seen = set()
    for msg in messages_user:
        key = (msg.logement_id, msg.etudiant_id)
        if key not in seen:
            discussions.append(msg)
            seen.add(key)

    return render_template("messages.html", discussions=discussions)


@app.route("/messages/<int:logement_id>/<int:etudiant_id>", methods=["GET", "POST"])
@login_required
def discussion(logement_id, etudiant_id):
    logement = Logement.query.get_or_404(logement_id)
    etudiant = Etudiant.query.get_or_404(etudiant_id)

    if current_user.role == "etudiant":
        allowed = current_user.etudiant.id == etudiant.id
    elif current_user.role == "proprietaire":
        allowed = logement.proprietaire_id == current_user.proprietaire.id
    else:
        allowed = False

    if not allowed:
        flash("Discussion inaccessible pour ce compte.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        contenu = request.form.get("contenu", "").strip()
        sujet = request.form.get("sujet", "").strip() or f"Discussion - {logement.titre}"
        if not contenu:
            flash("Le message ne peut pas Ãªtre vide.", "error")
            return redirect(url_for("discussion", logement_id=logement.id, etudiant_id=etudiant.id))

        db.session.add(
            Message(
                logement_id=logement.id,
                etudiant_id=etudiant.id,
                proprietaire_id=logement.proprietaire_id,
                expediteur_id=current_user.id,
                sujet=sujet,
                contenu=contenu,
            )
        )
        db.session.commit()
        flash("Message envoyÃ©.", "success")
        return redirect(url_for("discussion", logement_id=logement.id, etudiant_id=etudiant.id))

    messages_discussion = (
        Message.query.filter_by(logement_id=logement.id, etudiant_id=etudiant.id)
        .order_by(Message.id.asc())
        .all()
    )
    return render_template(
        "discussion.html",
        logement=logement,
        etudiant=etudiant,
        messages=messages_discussion,
    )


@app.route("/reservation/<int:id>")
@login_required
def reservation_detail(id):
    reservation = Reservation.query.get_or_404(id)
    return redirect(url_for("reservations"))


@app.route("/reservations")
@login_required
@role_required("etudiant")
def reservations():
    reservations_etudiant = Reservation.query.filter_by(etudiant_id=current_user.etudiant.id).all()
    return render_template("reservations.html", reservations=reservations_etudiant)


@app.route("/paiement/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("etudiant")
def paiement(id):
    reservation = Reservation.query.get_or_404(id)
    if reservation.etudiant_id != current_user.etudiant.id:
        flash("Reservation introuvable pour ce compte.", "error")
        return redirect(url_for("reservations"))
    flash("Le paiement en ligne n'est pas encore disponible sur StudentHome.", "error")
    return redirect(url_for("reservations"))


@app.route("/avis/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("etudiant")
def avis(id):
    reservation = Reservation.query.get_or_404(id)
    if reservation.statut_reservation not in ["Confirme", "ConfirmÃ©", "Termine", "TerminÃ©"]:
        flash("Vous pouvez laisser un avis aprÃ¨s confirmation ou fin de rÃ©servation.", "error")
        return redirect(url_for("reservations"))

    if request.method == "POST":
        avis_client = Avis(
            logement_id=reservation.logement_id,
            etudiant_id=current_user.etudiant.id,
            note=int(request.form["note"]),
            commentaire=request.form["commentaire"],
        )
        db.session.add(avis_client)
        db.session.commit()
        flash("Merci pour votre avis.", "success")
        return redirect(url_for("detail_logement", id=reservation.logement_id))

    return render_template("avis.html", reservation=reservation)


@app.route("/dashboard/etudiant")
@login_required
@role_required("etudiant")
def dashboard_etudiant():
    reservations_etudiant = Reservation.query.filter_by(etudiant_id=current_user.etudiant.id).all()
    favoris_count = Favori.query.filter_by(utilisateur_id=current_user.id).count()
    profil_coloc = current_user.etudiant.profil_colocation
    recommandations = []
    if profil_coloc:
        recommandations = sorted(
            Logement.query.filter_by(est_valide=True, est_bloque=False).all(),
            key=lambda logement: recommendation_score(logement, profil_coloc.budget, profil_coloc.faculte, "", logement.est_colocation),
            reverse=True,
        )[:3]
    return render_template(
        "dashboard_etudiant.html",
        reservations=reservations_etudiant,
        favoris_count=favoris_count,
        recommandations=recommandations,
    )


@app.route("/dashboard/proprietaire")
@login_required
@role_required("proprietaire")
def dashboard_proprietaire():
    logements_prop = (
        Logement.query.filter_by(proprietaire_id=current_user.proprietaire.id)
        .order_by(Logement.vues.desc(), Logement.id.desc())
        .all()
    )
    total_vues = sum((logement.vues or 0) for logement in logements_prop)
    annonce_plus_vue = logements_prop[0] if logements_prop else None
    demandes = (
        Reservation.query.join(Logement)
        .filter(Logement.proprietaire_id == current_user.proprietaire.id)
        .order_by(Reservation.id.desc())
        .all()
    )
    visites = Visite.query.filter_by(proprietaire_id=current_user.proprietaire.id).order_by(Visite.id.desc()).all()
    incidents = (
        Incident.query.join(Logement)
        .filter(Logement.proprietaire_id == current_user.proprietaire.id)
        .order_by(Incident.id.desc())
        .all()
    )
    return render_template(
        "dashboard_proprietaire.html",
        logements=logements_prop,
        total_vues=total_vues,
        annonce_plus_vue=annonce_plus_vue,
        demandes=demandes,
        visites=visites,
        incidents=incidents,
    )


@app.route("/dashboard/admin")
@login_required
@role_required("admin")
def dashboard_admin():
    stats = {
        "etudiants": Utilisateur.query.filter_by(role="etudiant").count(),
        "proprietaires": Utilisateur.query.filter_by(role="proprietaire").count(),
        "logements": Logement.query.count(),
        "reservations": Reservation.query.count(),
        "messages": Message.query.count(),
        "aide": SupportMessage.query.count(),
    }
    etudiants = Etudiant.query.join(Utilisateur).order_by(Utilisateur.id.desc()).all()
    proprietaires = Proprietaire.query.join(Utilisateur).order_by(Utilisateur.id.desc()).all()
    logements = Logement.query.order_by(Logement.id.desc()).limit(8).all()
    reservations = Reservation.query.order_by(Reservation.id.desc()).limit(8).all()
    messages_recents = Message.query.order_by(Message.id.desc()).limit(8).all()
    support_messages = SupportMessage.query.order_by(SupportMessage.id.desc()).limit(12).all()

    activites = []
    for logement in logements[:5]:
        activites.append({
            "type": "Annonce",
            "titre": logement.titre,
            "detail": f"{logement.proprietaire.utilisateur.nom} - {logement.quartier}",
            "date": f"#{logement.id}",
        })
    for reservation in reservations[:5]:
        activites.append({
            "type": "RÃ©servation",
            "titre": reservation.logement.titre,
            "detail": f"{reservation.etudiant.utilisateur.nom} - {reservation.statut_reservation}",
            "date": f"#{reservation.id}",
        })
    for message in messages_recents[:5]:
        activites.append({
            "type": "Message",
            "titre": message.logement.titre,
            "detail": f"{message.expediteur.nom} : {message.contenu[:70]}",
            "date": message.date_envoi,
        })
    for support in support_messages[:5]:
        activites.append({
            "type": "Aide",
            "titre": support.sujet,
            "detail": f"{support.nom} : {support.contenu[:70]}",
            "date": support.date_envoi,
        })

    return render_template(
        "dashboard_admin.html",
        stats=stats,
        etudiants=etudiants,
        proprietaires=proprietaires,
        activites=activites[:12],
        logements=logements,
        reservations=reservations,
        messages_recents=messages_recents,
        support_messages=support_messages,
    )


@app.route("/colocation", methods=["GET", "POST"])
@login_required
@role_required("etudiant")
def colocation():
    profil = current_user.etudiant.profil_colocation
    if request.method == "POST":
        if not profil:
            profil = ProfilColocation(etudiant_id=current_user.etudiant.id, faculte=current_user.etudiant.faculte_uca)
            db.session.add(profil)
        profil.budget = float(request.form.get("budget") or 0)
        profil.faculte = request.form.get("faculte", current_user.etudiant.faculte_uca)
        profil.fumeur = request.form.get("fumeur", "non")
        annee = int(request.form.get("annee_universitaire") or 1)
        profil.annee_universitaire = min(max(annee, 1), 5)
        db.session.commit()
        flash("Profil colocation mis a jour.", "success")
        return redirect(url_for("colocation"))

    profils = ProfilColocation.query.filter(ProfilColocation.etudiant_id != current_user.etudiant.id).all()
    matches = []
    if profil:
        for autre in profils:
            score = 0
            for champ in ["faculte", "fumeur", "annee_universitaire"]:
                if getattr(profil, champ) == getattr(autre, champ):
                    score += 18
            if profil.budget and autre.budget:
                score += max(0, 25 - int(abs(profil.budget - autre.budget) / 100))
            matches.append({"profil": autre, "score": min(score, 100)})
        matches.sort(key=lambda item: item["score"], reverse=True)
    return render_template("colocation.html", profil=profil, matches=matches[:6], facultes=FACULTES_UCA)


@app.route("/budget-colocation", methods=["POST"])
@login_required
def budget_colocation():
    total = sum(float(request.form.get(champ) or 0) for champ in ["loyer", "charges", "internet", "eau"])
    personnes = max(1, int(request.form.get("personnes") or 1))
    return render_template("budget_colocation.html", total=total, personnes=personnes, part=round(total / personnes, 2))


@app.route("/coffre-fort", methods=["GET", "POST"])
@login_required
def coffre_fort():
    if request.method == "POST":
        fichier = save_uploaded_document(request.files.get("document"))
        if not fichier:
            flash("Ajoutez un document valide.", "error")
            return redirect(url_for("coffre_fort"))
        db.session.add(
            Document(
                utilisateur_id=current_user.id,
                type_document=request.form.get("type_document", "Document"),
                fichier=fichier,
            )
        )
        db.session.commit()
        flash("Document ajoute au coffre-fort.", "success")
        return redirect(url_for("coffre_fort"))
    documents = Document.query.filter_by(utilisateur_id=current_user.id).order_by(Document.id.desc()).all()
    return render_template("coffre_fort.html", documents=documents)


@app.route("/contrat/<int:id>", methods=["GET", "POST"])
@login_required
def contrat(id):
    reservation = Reservation.query.get_or_404(id)
    if current_user.role == "etudiant" and reservation.etudiant_id != current_user.etudiant.id:
        flash("Contrat inaccessible.", "error")
        return redirect(url_for("reservations"))
    if current_user.role == "proprietaire" and reservation.logement.proprietaire_id != current_user.proprietaire.id:
        flash("Contrat inaccessible.", "error")
        return redirect(url_for("dashboard_proprietaire"))

    if request.method == "POST":
        duree = request.form.get("duree", "12")
        caution = request.form.get("caution", "1")
        charges = request.form.get("charges", "non")
        lines = [
            "%PDF-1.4",
            "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
            "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
            "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj",
        ]
        text = (
            f"BT /F1 18 Tf 60 760 Td (Student Home - Contrat de location) Tj "
            f"0 -40 Td /F1 12 Tf (Logement: {reservation.logement.titre}) Tj "
            f"0 -24 Td (Etudiant: {reservation.etudiant.utilisateur.nom}) Tj "
            f"0 -24 Td (Proprietaire: {reservation.logement.proprietaire.utilisateur.nom}) Tj "
            f"0 -24 Td (Duree: {duree} mois) Tj "
            f"0 -24 Td (Caution: {caution} mois) Tj "
            f"0 -24 Td (Charges incluses: {charges}) Tj "
            f"0 -80 Td /F1 30 Tf (Student Home) Tj ET"
        )
        stream = f"4 0 obj << /Length {len(text)} >> stream\n{text}\nendstream endobj"
        lines.append(stream)
        lines.append("5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj")
        lines.append("trailer << /Root 1 0 R >>\n%%EOF")
        pdf = "\n".join(lines).encode("latin-1", errors="ignore")
        return send_file(io.BytesIO(pdf), mimetype="application/pdf", as_attachment=True, download_name="contrat_studenthome.pdf")
    return render_template("contrat.html", reservation=reservation)


@app.route("/ajouter-annonce", methods=["GET", "POST"])
@login_required
@role_required("proprietaire")
def ajouter_annonce():
    if request.method == "POST":
        description = request.form["description"].strip()
        uploaded_media, media_error = save_uploaded_media_list(request.files.getlist("media"))

        if not description_has_max_30_lines(description):
            flash("La description ne doit pas dÃ©passer 30 lignes.", "error")
            return redirect(url_for("ajouter_annonce"))
        if media_error:
            flash(media_error, "error")
            return redirect(url_for("ajouter_annonce"))

        logement = Logement(
            titre=request.form["titre"].strip(),
            adresse=request.form.get("adresse", "").strip(),
            description=description,
            reglement_interieur=request.form.get("reglement_interieur", "").strip(),
            prix=float(request.form["prix"]),
            quartier=request.form["quartier"].strip(),
            proximite_faculte=request.form["proximite_faculte"].strip(),
            type_logement=request.form["type_logement"],
            nombre_chambres=int(request.form.get("nombre_chambres") or 1),
            etage=int(request.form.get("etage") or 0),
            latitude=float(request.form["latitude"]) if request.form.get("latitude") else guess_coordinates(request.form["quartier"].strip())[0],
            longitude=float(request.form["longitude"]) if request.form.get("longitude") else guess_coordinates(request.form["quartier"].strip())[1],
            est_colocation=request.form.get("est_colocation") == "1",
            photos=(uploaded_media[0] if uploaded_media else request.form.get("photos") or "marrakech-rooftop-sunset.jpg"),
            est_disponible=True,
            date_disponibilite=request.form["date_disponibilite"],
            est_valide=True,
            proprietaire_id=current_user.proprietaire.id,
        )
        db.session.add(logement)
        db.session.flush()
        for ordre, media_path in enumerate(uploaded_media):
            db.session.add(LogementMedia(logement_id=logement.id, fichier=media_path, ordre=ordre))
        db.session.commit()
        flash("Annonce ajoutÃ©e avec succÃ¨s. Elle est maintenant visible dans les logements.", "success")
        return redirect(url_for("dashboard_proprietaire"))
    return render_template("ajouter_annonce.html", logement=None)


@app.route("/modifier-annonce/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("proprietaire")
def modifier_annonce(id):
    logement = Logement.query.get_or_404(id)
    if logement.proprietaire_id != current_user.proprietaire.id:
        flash("Vous ne pouvez modifier que vos annonces.", "error")
        return redirect(url_for("dashboard_proprietaire"))

    if request.method == "POST":
        description = request.form["description"].strip()
        uploaded_media, media_error = save_uploaded_media_list(request.files.getlist("media"))

        if not description_has_max_30_lines(description):
            flash("La description ne doit pas dÃ©passer 30 lignes.", "error")
            return redirect(url_for("modifier_annonce", id=logement.id))
        if media_error:
            flash(media_error, "error")
            return redirect(url_for("modifier_annonce", id=logement.id))

        logement.titre = request.form["titre"].strip()
        logement.adresse = request.form.get("adresse", "").strip()
        logement.description = description
        logement.reglement_interieur = request.form.get("reglement_interieur", "").strip()
        logement.prix = float(request.form["prix"])
        logement.quartier = request.form["quartier"].strip()
        logement.proximite_faculte = request.form["proximite_faculte"].strip()
        logement.type_logement = request.form["type_logement"]
        logement.nombre_chambres = int(request.form.get("nombre_chambres") or 1)
        logement.etage = int(request.form.get("etage") or 0)
        logement.latitude = float(request.form["latitude"]) if request.form.get("latitude") else guess_coordinates(logement.quartier)[0]
        logement.longitude = float(request.form["longitude"]) if request.form.get("longitude") else guess_coordinates(logement.quartier)[1]
        logement.est_colocation = request.form.get("est_colocation") == "1"
        if uploaded_media:
            logement.photos = uploaded_media[0]
            next_order = len(logement.medias)
            for index, media_path in enumerate(uploaded_media):
                db.session.add(LogementMedia(logement_id=logement.id, fichier=media_path, ordre=next_order + index))
        elif request.form.get("photos") and not logement.medias and not (logement.photos or "").startswith("uploads/"):
            logement.photos = request.form.get("photos")
        logement.est_disponible = True
        logement.date_disponibilite = request.form["date_disponibilite"]
        logement.est_valide = True
        db.session.commit()
        flash("Annonce modifiÃ©e avec succÃ¨s.", "success")
        return redirect(url_for("dashboard_proprietaire"))
    return render_template("ajouter_annonce.html", logement=logement)


@app.route("/supprimer-annonce/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("proprietaire")
def supprimer_annonce(id):
    logement = Logement.query.get_or_404(id)
    if logement.proprietaire_id != current_user.proprietaire.id:
        flash("Vous ne pouvez supprimer que vos annonces.", "error")
        return redirect(url_for("dashboard_proprietaire"))

    Favori.query.filter_by(logement_id=logement.id).delete()
    Message.query.filter_by(logement_id=logement.id).delete()
    Visite.query.filter_by(logement_id=logement.id).delete()
    Incident.query.filter_by(logement_id=logement.id).delete()
    InventaireItem.query.filter_by(logement_id=logement.id).delete()
    LogementMedia.query.filter_by(logement_id=logement.id).delete()
    Avis.query.filter_by(logement_id=logement.id).delete()
    Reservation.query.filter_by(logement_id=logement.id).delete()
    db.session.delete(logement)
    db.session.commit()
    if True:
        flash("Annonce supprimÃ©e.", "success")
    return redirect(url_for("dashboard_proprietaire"))


@app.route("/accepter-reservation/<int:id>")
@login_required
@role_required("proprietaire")
def accepter_reservation(id):
    reservation = Reservation.query.get_or_404(id)
    if reservation.logement.proprietaire_id == current_user.proprietaire.id:
        reservation.statut_reservation = "Confirme"
        reservation.statut_paiement = "Non disponible"
        db.session.commit()
        flash("Demande acceptee. La reservation est confirmee.", "success")
    return redirect(url_for("dashboard_proprietaire"))


@app.route("/refuser-reservation/<int:id>")
@login_required
@role_required("proprietaire")
def refuser_reservation(id):
    reservation = Reservation.query.get_or_404(id)
    if reservation.logement.proprietaire_id == current_user.proprietaire.id:
        reservation.statut_reservation = "RefusÃ©"
        db.session.commit()
        flash("Demande refusÃ©e.", "success")
    return redirect(url_for("dashboard_proprietaire"))


@app.route("/confirmer-conformite/<int:id>")
@login_required
@role_required("proprietaire")
def confirmer_conformite(id):
    reservation = Reservation.query.get_or_404(id)
    if reservation.logement.proprietaire_id == current_user.proprietaire.id:
        reservation.statut_reservation = "TerminÃ©"
        db.session.commit()
        flash("Logement confirmÃ© conforme. RÃ©servation terminÃ©e.", "success")
    return redirect(url_for("dashboard_proprietaire"))


with app.app_context():
    init_database()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)


