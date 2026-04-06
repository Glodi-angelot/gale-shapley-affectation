import sys
import csv
import json
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
    QSpinBox,
    QComboBox,
    QTextEdit,
    QGroupBox,
    QHeaderView,
    QTabWidget,
    QSplitter,
    QLineEdit,
    QFrame,
    QSizePolicy,
)


@dataclass
class Student:
    name: str
    profile: str
    score: int


@dataclass
class University:
    name: str
    specialty: str


PROFILES = [
    "Informatique",
    "Mathématiques",
    "Statistique",
    "Gestion",
    "Communication",
    "Santé",
    "Pédagogie",
    "Arts",
]

UNIVERSITY_POOL = [
    ("UNIKIN", "Informatique"),
    ("UNILU", "Mathématiques"),
    ("UPN", "Pédagogie"),
    ("ISTA", "Informatique"),
    ("ISC", "Gestion"),
    ("ISTM", "Santé"),
    ("UNISIC", "Communication"),
    ("ISP-Gombe", "Pédagogie"),
    ("UPC", "Informatique"),
    ("UCC", "Gestion"),
    ("UCB", "Santé"),
    ("ULK", "Communication"),
    ("UNIKI", "Mathématiques"),
    ("UNIGOM", "Statistique"),
    ("UOR", "Arts"),
    ("UNIBU", "Gestion"),
]

PROFILE_PRIORITY = {
    "Informatique": ["Informatique", "Mathématiques", "Statistique", "Gestion", "Communication", "Pédagogie", "Santé", "Arts"],
    "Mathématiques": ["Mathématiques", "Statistique", "Informatique", "Pédagogie", "Gestion", "Communication", "Santé", "Arts"],
    "Statistique": ["Statistique", "Mathématiques", "Informatique", "Gestion", "Communication", "Pédagogie", "Santé", "Arts"],
    "Gestion": ["Gestion", "Communication", "Statistique", "Informatique", "Mathématiques", "Pédagogie", "Santé", "Arts"],
    "Communication": ["Communication", "Gestion", "Arts", "Pédagogie", "Informatique", "Statistique", "Mathématiques", "Santé"],
    "Santé": ["Santé", "Mathématiques", "Statistique", "Pédagogie", "Communication", "Gestion", "Informatique", "Arts"],
    "Pédagogie": ["Pédagogie", "Communication", "Mathématiques", "Gestion", "Informatique", "Statistique", "Santé", "Arts"],
    "Arts": ["Arts", "Communication", "Gestion", "Pédagogie", "Informatique", "Mathématiques", "Statistique", "Santé"],
}


# Génère une population d'étudiants avec profil et score.
def generate_students(n: int) -> List[Student]:
    students: List[Student] = []
    for i in range(1, n + 1):
        profile = random.choice(PROFILES)
        score = random.randint(50, 95)
        students.append(Student(name=f"E{i}", profile=profile, score=score))
    return students


# Génère la liste des universités utilisées dans la simulation.
def generate_universities(n: int) -> List[University]:
    selected = UNIVERSITY_POOL[:]
    while len(selected) < n:
        idx = len(selected) + 1
        selected.append((f"U{idx}", random.choice(PROFILES)))
    return [University(name=name, specialty=specialty) for name, specialty in selected[:n]]


# Préférences des étudiants : priorité aux universités proches de leur profil.
def build_student_preferences(students: List[Student], universities: List[University]) -> Dict[str, List[str]]:
    preferences: Dict[str, List[str]] = {}
    for student in students:
        ranked = sorted(
            universities,
            key=lambda u: (
                PROFILE_PRIORITY[student.profile].index(u.specialty),
                random.random(),
            ),
        )
        preferences[student.name] = [u.name for u in ranked]
    return preferences


# Préférences des universités : priorité au bon profil puis au score.
def build_university_preferences(students: List[Student], universities: List[University]) -> Dict[str, List[str]]:
    preferences: Dict[str, List[str]] = {}
    for university in universities:
        ranked = sorted(
            students,
            key=lambda s: (
                0 if s.profile == university.specialty else 1,
                -s.score,
                s.name,
            ),
        )
        preferences[university.name] = [s.name for s in ranked]
    return preferences


# Implémentation de Gale-Shapley côté étudiants proposants.
def gale_shapley(student_prefs: Dict[str, List[str]], uni_prefs: Dict[str, List[str]]) -> Tuple[Dict[str, str], int]:
    free_students = list(student_prefs.keys())
    next_choice_index = {s: 0 for s in student_prefs}
    engagements: Dict[str, str] = {}  # université -> étudiant
    proposals = 0

    uni_rank = {
        u: {student: rank for rank, student in enumerate(pref_list)}
        for u, pref_list in uni_prefs.items()
    }

    while free_students:
        student = free_students.pop(0)
        if next_choice_index[student] >= len(student_prefs[student]):
            continue

        university = student_prefs[student][next_choice_index[student]]
        next_choice_index[student] += 1
        proposals += 1

        if university not in engagements:
            engagements[university] = student
        else:
            current_student = engagements[university]
            if uni_rank[university][student] < uni_rank[university][current_student]:
                engagements[university] = student
                free_students.append(current_student)
            else:
                free_students.append(student)

    matching = {student: university for university, student in engagements.items()}
    return matching, proposals


# Détecte les éventuelles paires bloquantes après l'affectation.
def find_blocking_pairs(
    matching: Dict[str, str],
    student_prefs: Dict[str, List[str]],
    uni_prefs: Dict[str, List[str]],
) -> List[Tuple[str, str]]:
    reverse_matching = {u: s for s, u in matching.items()}
    uni_rank = {
        u: {student: rank for rank, student in enumerate(pref_list)}
        for u, pref_list in uni_prefs.items()
    }

    blocking_pairs: List[Tuple[str, str]] = []
    for student, current_uni in matching.items():
        preferred_unis = student_prefs[student][: student_prefs[student].index(current_uni)]
        for uni in preferred_unis:
            current_student_at_uni = reverse_matching.get(uni)
            if current_student_at_uni is None:
                blocking_pairs.append((student, uni))
                continue
            if uni_rank[uni][student] < uni_rank[uni][current_student_at_uni]:
                blocking_pairs.append((student, uni))
    return blocking_pairs


# Mesures simples pour le résumé analytique.
def satisfaction_stats(matching: Dict[str, str], student_prefs: Dict[str, List[str]]) -> Dict[str, float]:
    total = len(matching) if matching else 1
    first = 0
    top3 = 0
    ranks = []

    for student, university in matching.items():
        rank = student_prefs[student].index(university) + 1
        ranks.append(rank)
        if rank == 1:
            first += 1
        if rank <= 3:
            top3 += 1

    avg_rank = sum(ranks) / len(ranks) if ranks else 0.0
    return {
        "first_choice_pct": round((first / total) * 100, 2),
        "top3_pct": round((top3 / total) * 100, 2),
        "avg_rank": round(avg_rank, 2),
    }


class TableFactory:
    @staticmethod
    def make_table(columns: List[str]) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setShowGrid(True)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table.setStyleSheet(
            """
            QTableWidget {
                background: #ffffff;
                alternate-background-color: #f8fbff;
                gridline-color: #dbe4ee;
                border: 1px solid #dbe4ee;
                border-radius: 12px;
                padding: 6px;
            }
            QHeaderView::section {
                background: #1f4e79;
                color: white;
                padding: 10px;
                border: none;
                font-weight: 700;
            }
            """
        )
        return table


class InfoPill(QFrame):
    def __init__(self, title: str, value: str = "-"):
        super().__init__()
        self.title_label = QLabel(title)
        self.value_label = QLabel(value)

        self.title_label.setStyleSheet("color:#607a94; font-size:12px; font-weight:600;")
        self.value_label.setStyleSheet("color:#173b56; font-size:18px; font-weight:800;")
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)
        layout.addWidget(self.title_label)
        layout.addStretch(1)
        layout.addWidget(self.value_label)

        self.setStyleSheet(
            """
            QFrame {
                background: white;
                border: 1px solid #dbe4ee;
                border-radius: 12px;
            }
            """
        )

    def set_value(self, value: str):
        self.value_label.setText(value)

    def set_value_color(self, color: str):
        self.value_label.setStyleSheet(
            f"color:{color}; font-size:18px; font-weight:800;"
        )

    def reset_default_color(self):
        self.value_label.setStyleSheet("color:#173b56; font-size:18px; font-weight:800;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Système d'affectation universitaire stable — Gale-Shapley")
        self.resize(1560, 940)
        self.setMinimumSize(1220, 760)

        self.students: List[Student] = []
        self.universities: List[University] = []
        self.student_prefs: Dict[str, List[str]] = {}
        self.uni_prefs: Dict[str, List[str]] = {}
        self.matching: Dict[str, str] = {}
        self.last_proposals: int = 0

        self._build_ui()
        self.generate_dataset()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        header = self._build_header()
        toolbar = self._build_toolbar()
        summary = self._build_summary_bar()

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self._build_left_panel())
        self.splitter.addWidget(self._build_right_panel())
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setSizes([340, 1180])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        main_layout.addWidget(header)
        main_layout.addWidget(toolbar)
        main_layout.addWidget(summary)
        main_layout.addWidget(self.splitter, 1)

        root.setStyleSheet(
            """
            QWidget {
                background: #eef4f9;
                color: #172b3a;
                font-size: 12px;
            }
            QGroupBox {
                background: white;
                border: 1px solid #dbe4ee;
                border-radius: 16px;
                margin-top: 12px;
                font-weight: 700;
                color: #173b56;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
            }
            QPushButton {
                background-color: #1f4e79;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #2c618f;
            }
            QPushButton:pressed {
                background-color: #163d60;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                background: white;
                border: 1px solid #cfd9e3;
                border-radius: 10px;
                padding: 8px;
            }
            QTabWidget::pane {
                border: 1px solid #dbe4ee;
                background: white;
                border-radius: 12px;
            }
            QTabBar::tab {
                background: #e9f0f7;
                padding: 10px 14px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #1f4e79;
                color: white;
                font-weight: 700;
            }
            """
        )

    def _build_header(self) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #153a5b, stop:1 #295f91);
                border-radius: 18px;
            }
            QLabel {
                background: transparent;
                color: white;
            }
            """
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(6)

        title = QLabel("Affectation universitaire par l'algorithme de Gale-Shapley")
        title.setFont(QFont("Arial", 18, QFont.Bold))

        subtitle = QLabel(
            "Simulation complète, génération des préférences, exécution, vérification de stabilité et export des résultats"
        )
        subtitle.setStyleSheet("font-size: 12px; color: #e4eef8;")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return frame

    def _build_toolbar(self) -> QWidget:
        box = QGroupBox("Paramètres et actions")
        layout = QHBoxLayout(box)
        layout.setContentsMargins(14, 16, 14, 12)
        layout.setSpacing(10)

        self.count_spin = QSpinBox()
        self.count_spin.setRange(3, 50)
        self.count_spin.setValue(8)
        self.count_spin.setPrefix("Taille : ")

        self.seed_input = QLineEdit()
        self.seed_input.setPlaceholderText("Graine aléatoire (facultative)")
        self.seed_input.setMaximumWidth(220)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Simulation réaliste", "Simulation aléatoire guidée"])
        self.theme_combo.setMinimumWidth(210)

        btn_generate = QPushButton("Générer les données")
        btn_generate.clicked.connect(self.generate_dataset)

        btn_run = QPushButton("Lancer l'affectation")
        btn_run.clicked.connect(self.run_algorithm)

        btn_reset = QPushButton("Réinitialiser")
        btn_reset.clicked.connect(self.reset_app)

        btn_export = QPushButton("Exporter en CSV")
        btn_export.clicked.connect(self.export_csv)

        btn_save_json = QPushButton("Sauvegarder JSON")
        btn_save_json.clicked.connect(self.save_json)

        btn_load_json = QPushButton("Charger JSON")
        btn_load_json.clicked.connect(self.load_json)

        for widget in [
            self.count_spin,
            self.seed_input,
            self.theme_combo,
            btn_generate,
            btn_run,
            btn_reset,
            btn_export,
            btn_save_json,
            btn_load_json,
        ]:
            layout.addWidget(widget)

        layout.addStretch(1)
        return box

    # Barre de synthèse horizontale à la place de l'ancien tableau de bord.
    def _build_summary_bar(self) -> QWidget:
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.pill_students = InfoPill("Étudiants")
        self.pill_unis = InfoPill("Universités")
        self.pill_proposals = InfoPill("Propositions")
        self.pill_stability = InfoPill("Stabilité")
        self.pill_first = InfoPill("Premier choix")
        self.pill_top3 = InfoPill("Trois premiers choix")

        for pill in [
            self.pill_students,
            self.pill_unis,
            self.pill_proposals,
            self.pill_stability,
            self.pill_first,
            self.pill_top3,
        ]:
            layout.addWidget(pill)

        return frame

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMaximumWidth(360)
        panel.setMinimumWidth(300)
        panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        notes_box = QGroupBox("Résumé analytique")
        notes_layout = QVBoxLayout(notes_box)
        notes_layout.setContentsMargins(12, 18, 12, 12)
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMinimumHeight(260)
        self.analysis_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        notes_layout.addWidget(self.analysis_text)
        layout.addWidget(notes_box, 2)

        profile_box = QGroupBox("Profils disciplinaires")
        profile_layout = QVBoxLayout(profile_box)
        profile_layout.setContentsMargins(12, 18, 12, 12)
        self.profile_info = QTextEdit()
        self.profile_info.setReadOnly(True)
        self.profile_info.setMinimumHeight(210)
        self.profile_info.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        profile_layout.addWidget(self.profile_info)
        layout.addWidget(profile_box, 1)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.students_table = TableFactory.make_table(["Étudiant", "Profil", "Score"])
        self.unis_table = TableFactory.make_table(["Université", "Spécialité"])
        self.student_pref_table = TableFactory.make_table(["Étudiant", "Préférences"])
        self.uni_pref_table = TableFactory.make_table(["Université", "Préférences"])
        self.result_table = TableFactory.make_table(["Étudiant", "Université attribuée", "Rang obtenu"])
        self.blocking_table = TableFactory.make_table(["Étudiant", "Université"])

        self.tabs.addTab(self._wrap_widget(self.students_table), "Étudiants")
        self.tabs.addTab(self._wrap_widget(self.unis_table), "Universités")
        self.tabs.addTab(self._wrap_widget(self.student_pref_table), "Préférences étudiants")
        self.tabs.addTab(self._wrap_widget(self.uni_pref_table), "Préférences universités")
        self.tabs.addTab(self._wrap_widget(self.result_table), "Résultats")
        self.tabs.addTab(self._build_stability_tab(), "Stabilité")
        self.tabs.addTab(self._build_synthesis_tab(), "Synthèse")

        layout.addWidget(self.tabs)
        return panel

    def _wrap_widget(self, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(widget)
        return container

    # Onglet stabilité enrichi : message explicite + tableau.
    def _build_stability_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.stability_banner = QLabel("Aucune vérification effectuée pour le moment.")
        self.stability_banner.setWordWrap(True)
        self.stability_banner.setStyleSheet(
            "background:#eef5fb; border:1px solid #dbe4ee; border-radius:10px; padding:10px; color:#173b56; font-weight:600;"
        )

        layout.addWidget(self.stability_banner)
        layout.addWidget(self.blocking_table, 1)
        return container

    # Onglet synthèse pour la soutenance.
    def _build_synthesis_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)

        self.summary_global = QTextEdit()
        self.summary_global.setReadOnly(True)
        self.summary_global.setStyleSheet(
            "background:#ffffff; border:1px solid #dbe4ee; border-radius:10px; padding:10px;"
        )

        layout.addWidget(self.summary_global)
        return container

    def generate_dataset(self):
        seed_text = self.seed_input.text().strip()
        if seed_text:
            try:
                random.seed(int(seed_text))
            except ValueError:
                random.seed(seed_text)
        else:
            random.seed()

        n = self.count_spin.value()
        self.students = generate_students(n)
        self.universities = generate_universities(n)
        self.student_prefs = build_student_preferences(self.students, self.universities)
        self.uni_prefs = build_university_preferences(self.students, self.universities)
        self.matching = {}
        self.last_proposals = 0

        self.populate_all_tables()
        self.update_summary_bar()
        self.stability_banner.setText(
            "Jeu de données prêt. Lancez l'affectation pour vérifier la stabilité de l'appariement."
        )
        self.summary_global.setPlainText("Aucune exécution effectuée pour le moment.")
        self.analysis_text.setPlainText(
            "Jeu de données généré avec succès.\n\n"
            "Vous pouvez maintenant examiner les profils, les préférences, puis lancer l'algorithme de Gale-Shapley afin d'obtenir une affectation stable et analysable."
        )

    def populate_all_tables(self):
        self._fill_students_table()
        self._fill_universities_table()
        self._fill_student_pref_table()
        self._fill_uni_pref_table()
        self._fill_result_table()
        self._fill_blocking_table([])
        self._fill_profile_info()

    def _fill_students_table(self):
        self.students_table.setRowCount(len(self.students))
        for row, student in enumerate(self.students):
            self.students_table.setItem(row, 0, QTableWidgetItem(student.name))
            self.students_table.setItem(row, 1, QTableWidgetItem(student.profile))
            self.students_table.setItem(row, 2, QTableWidgetItem(str(student.score)))

    def _fill_universities_table(self):
        self.unis_table.setRowCount(len(self.universities))
        for row, university in enumerate(self.universities):
            self.unis_table.setItem(row, 0, QTableWidgetItem(university.name))
            self.unis_table.setItem(row, 1, QTableWidgetItem(university.specialty))

    def _fill_student_pref_table(self):
        students = list(self.student_prefs.keys())
        self.student_pref_table.setRowCount(len(students))
        for row, student in enumerate(students):
            self.student_pref_table.setItem(row, 0, QTableWidgetItem(student))
            self.student_pref_table.setItem(row, 1, QTableWidgetItem(" > ".join(self.student_prefs[student])))

    def _fill_uni_pref_table(self):
        universities = list(self.uni_prefs.keys())
        self.uni_pref_table.setRowCount(len(universities))
        for row, university in enumerate(universities):
            self.uni_pref_table.setItem(row, 0, QTableWidgetItem(university))
            self.uni_pref_table.setItem(row, 1, QTableWidgetItem(" > ".join(self.uni_prefs[university])))

    def _fill_result_table(self):
        rows = sorted(self.matching.items())
        self.result_table.setRowCount(len(rows))
        for row, (student, university) in enumerate(rows):
            rank = self.student_prefs[student].index(university) + 1
            self.result_table.setItem(row, 0, QTableWidgetItem(student))
            self.result_table.setItem(row, 1, QTableWidgetItem(university))
            self.result_table.setItem(row, 2, QTableWidgetItem(str(rank)))

    def _fill_blocking_table(self, blocking_pairs: List[Tuple[str, str]]):
        if not blocking_pairs:
            self.blocking_table.setRowCount(1)
            self.blocking_table.setItem(0, 0, QTableWidgetItem("Aucune paire bloquante"))
            self.blocking_table.setItem(0, 1, QTableWidgetItem("-"))
            return

        self.blocking_table.setRowCount(len(blocking_pairs))
        for row, (student, university) in enumerate(blocking_pairs):
            self.blocking_table.setItem(row, 0, QTableWidgetItem(student))
            self.blocking_table.setItem(row, 1, QTableWidgetItem(university))

    def _fill_profile_info(self):
        grouped: Dict[str, int] = {}
        for student in self.students:
            grouped[student.profile] = grouped.get(student.profile, 0) + 1

        lines = ["Répartition des profils présents dans l'instance :", ""]
        for profile in sorted(grouped.keys()):
            lines.append(f"- {profile} : {grouped[profile]} étudiant(s)")
        self.profile_info.setPlainText("\n".join(lines))

    def run_algorithm(self):
        if not self.student_prefs or not self.uni_prefs:
            QMessageBox.warning(self, "Données manquantes", "Veuillez d'abord générer ou charger un jeu de données.")
            return

        self.matching, self.last_proposals = gale_shapley(self.student_prefs, self.uni_prefs)
        blocking_pairs = find_blocking_pairs(self.matching, self.student_prefs, self.uni_prefs)
        stats = satisfaction_stats(self.matching, self.student_prefs)

        self._fill_result_table()
        self._fill_blocking_table(blocking_pairs)
        self.update_summary_bar(stats, blocking_pairs)
        self.update_global_summary(stats, blocking_pairs)

        if not blocking_pairs:
            self.stability_banner.setText(
                "Affectation terminée avec succès — aucun couple étudiant–université ne souhaite dévier. L'appariement obtenu est stable."
            )
        else:
            self.stability_banner.setText(
                f"Attention : {len(blocking_pairs)} paire(s) bloquante(s) ont été détectées. L'appariement est instable."
            )

        analysis = [
            "Résultat de l'exécution de Gale-Shapley",
            "",
            f"- Nombre d'étudiants affectés : {len(self.matching)} / {len(self.students)}",
            f"- Nombre total de propositions : {self.last_proposals}",
            f"- Pourcentage d'étudiants obtenant leur premier choix : {stats['first_choice_pct']}%",
            f"- Pourcentage d'étudiants obtenant l'un de leurs trois premiers choix : {stats['top3_pct']}%",
            f"- Rang moyen de l'affectation obtenue : {stats['avg_rank']}",
            f"- Nombre de paires bloquantes détectées : {len(blocking_pairs)}",
            "",
        ]

        if not blocking_pairs:
            analysis.append(
                "Affectation terminée avec succès — appariement stable obtenu."
            )
        else:
            analysis.append(
                "Attention : des paires bloquantes ont été détectées."
            )

        analysis.extend([
            "",
            "Lecture du résultat :",
            "Comme les étudiants sont les proposants, la solution obtenue leur est la plus favorable parmi les appariements stables possibles.",
        ])
        self.analysis_text.setPlainText("\n".join(analysis))
        QMessageBox.information(self, "Exécution terminée", "L'affectation a été calculée avec succès.")

    def update_summary_bar(self, stats: Dict[str, float] = None, blocking_pairs: List[Tuple[str, str]] = None):
        self.pill_students.set_value(str(len(self.students)))
        self.pill_unis.set_value(str(len(self.universities)))
        self.pill_proposals.set_value(str(self.last_proposals))

        self.pill_stability.reset_default_color()

        if stats is None:
            self.pill_stability.set_value("-")
            self.pill_first.set_value("0%")
            self.pill_top3.set_value("0%")
            return

        if not blocking_pairs:
            self.pill_stability.set_value("Stable")
            self.pill_stability.set_value_color("green")
        else:
            self.pill_stability.set_value("Instable")
            self.pill_stability.set_value_color("red")

        self.pill_first.set_value(f"{stats['first_choice_pct']}%")
        self.pill_top3.set_value(f"{stats['top3_pct']}%")

    def update_global_summary(self, stats: Dict[str, float], blocking_pairs: List[Tuple[str, str]]):
        stable_text = "STABLE" if not blocking_pairs else "INSTABLE"
        text = (
            "AFFECTATION TERMINÉE\n\n"
            f"- Étudiants : {len(self.students)}\n"
            f"- Universités : {len(self.universities)}\n"
            f"- Étudiants affectés : {len(self.matching)}\n"
            f"- Propositions totales : {self.last_proposals}\n"
            f"- Premier choix : {stats['first_choice_pct']}%\n"
            f"- Trois premiers choix : {stats['top3_pct']}%\n"
            f"- Rang moyen obtenu : {stats['avg_rank']}\n"
            f"- Paires bloquantes : {len(blocking_pairs)}\n"
            f"- Statut final : {stable_text}\n"
        )
        self.summary_global.setPlainText(text)

    def reset_app(self):
        self.matching = {}
        self.last_proposals = 0
        self._fill_result_table()
        self._fill_blocking_table([])
        self.update_summary_bar()
        self.summary_global.setPlainText("Application réinitialisée.")
        self.stability_banner.setText("Réinitialisation effectuée. Générez ou rechargez un jeu de données, puis lancez l'affectation.")
        self.analysis_text.setPlainText("Application réinitialisée.")
        self.tabs.setCurrentIndex(0)

    def export_csv(self):
        if not self.matching:
            QMessageBox.warning(self, "Aucun résultat", "Exécutez d'abord l'algorithme avant d'exporter.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter les résultats",
            "resultats_affectation.csv",
            "CSV Files (*.csv)",
        )
        if not path:
            return

        student_map = {student.name: student for student in self.students}
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(["Étudiant", "Université attribuée", "Profil", "Score", "Rang obtenu"])
            for student, university in sorted(self.matching.items()):
                rank = self.student_prefs[student].index(university) + 1
                current = student_map[student]
                writer.writerow([student, university, current.profile, current.score, rank])

        QMessageBox.information(self, "Export réussi", "Les résultats ont été exportés en CSV.")

    def save_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder les données",
            "donnees_gale_shapley.json",
            "JSON Files (*.json)",
        )
        if not path:
            return

        data = {
            "students": [student.__dict__ for student in self.students],
            "universities": [university.__dict__ for university in self.universities],
            "student_prefs": self.student_prefs,
            "uni_prefs": self.uni_prefs,
        }
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

        QMessageBox.information(self, "Sauvegarde réussie", "Les données ont été sauvegardées en JSON.")

    def load_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Charger les données",
            "",
            "JSON Files (*.json)",
        )
        if not path:
            return

        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.students = [Student(**item) for item in data["students"]]
        self.universities = [University(**item) for item in data["universities"]]
        self.student_prefs = data["student_prefs"]
        self.uni_prefs = data["uni_prefs"]
        self.matching = {}
        self.last_proposals = 0

        self.populate_all_tables()
        self.update_summary_bar()
        self.stability_banner.setText("Jeu de données chargé. Lancez l'affectation pour contrôler la stabilité.")
        self.summary_global.setPlainText("Jeu de données chargé. Aucune exécution effectuée.")
        self.analysis_text.setPlainText(
            "Jeu de données chargé avec succès.\n\n"
            "Vous pouvez maintenant lancer l'algorithme pour calculer une nouvelle affectation stable."
        )
        QMessageBox.information(self, "Chargement réussi", "Les données ont été chargées depuis le fichier JSON.")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()