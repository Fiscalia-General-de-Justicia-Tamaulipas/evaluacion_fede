import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app import main
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


class SaveAnswerSecurityTests(unittest.TestCase):
    def setUp(self):
        self.evaluation = SimpleNamespace(
            id=24,
            user_id=7,
            module_id=1,
            completed_at=None,
            video_completed=True,
        )
        self.question = SimpleNamespace(id=11, module_id=1)
        self.option = SimpleNamespace(id=5, question_id=11, is_correct=True)
        self.database = Mock()
        self.database.get.side_effect = lambda model, _: {
            main.Evaluation: self.evaluation,
            main.Question: self.question,
            main.Option: self.option,
        }[model]
        self.user = SimpleNamespace(id=7)
        self.data = main.SaveAnswerIn(question_id=11, option_id=5)

    def save_answer(self, existing_answer=None):
        self.database.scalar.return_value = existing_answer
        with (
            patch.object(main, "_require_available_module"),
            patch.object(main, "get_evaluation_question_order", return_value=[11]),
            patch.object(main, "get_next_unanswered_index", return_value=0),
        ):
            return main.save_answer(24, self.data, self.database, self.user)

    def test_new_answer_does_not_disclose_correctness(self):
        response = self.save_answer()

        self.assertNotIn("is_correct", response)

    def test_updated_answer_does_not_disclose_correctness(self):
        existing_answer = SimpleNamespace(option_id=4, is_correct=False)

        response = self.save_answer(existing_answer)

        self.assertNotIn("is_correct", response)

    def test_answer_from_outside_the_selected_question_order_is_rejected(self):
        with (
            patch.object(main, "_require_available_module"),
            patch.object(main, "get_evaluation_question_order", return_value=[12]),
            self.assertRaises(main.HTTPException) as raised,
        ):
            main.save_answer(24, self.data, self.database, self.user)

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(
            raised.exception.detail,
            "La pregunta no forma parte de esta evaluación.",
        )


class ModuleOneQuestionSeedTests(unittest.TestCase):
    def test_seed_loads_the_provided_questions_and_answer_key(self):
        engine = create_engine("sqlite+pysqlite:///:memory:")
        main.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        expected_texts = [
            "¿Cuál es la característica del voto que implica que todo ciudadano debe votar de acuerdo con su preferencia política, o en favor del candidato, candidata o partido político que elija sin coacción o presión de ningún tipo?",
            "¿Cuál es la Autoridad Electoral encargada de organizar las elecciones federales?",
            "¿Cuál es la Autoridad Electoral que tiene como principales atribuciones, resolver las impugnaciones y controversias sobre elecciones federales así como realizar el cómputo final, calificar la legalidad y declarar al presidente electo de México?",
            "Es la Autoridad Electoral que tiene como principal atribución atender e investigar los delitos en materia electoral del fuero federal.",
            "¿Cuál de los siguientes cargos de elección popular no corresponde a un proceso electoral local?",
            "¿A qué mecanismo de protección de la democracia pertenecen las Fiscalías Especializadas en Delitos Electorales?",
            "Es la herramienta mediante la cual se ejerce la democracia, y es el pueblo en su conjunto quien ejerce su soberanía eligiendo a sus gobernantes mediante elecciones periódicas.",
            "Es la característica del voto que consiste en que cada ciudadano o ciudadana debe votar sin ser observado u observada.",
            "Es el tipo de Proceso Electoral, mediante el cual se eligen cargos públicos de elección popular federales como lo son Presidente de la República, Diputados Federales y Senadores.",
            "De conformidad con lo establecido en la Ley General de Instituciones y Procedimientos Electorales, ¿cómo se denomina al conjunto de reuniones públicas, asambleas, marchas y, en general, actos en los cuales las personas precandidatas se dirigen a sus afiliados, simpatizantes o al electorado para obtener su respaldo?",
        ]
        expected_correct_letters = [
            ["B"], ["D"], ["C"], ["B"], ["C"],
            ["C"], ["B"], ["C"], ["A"], ["A"],
        ]
        expected_option_letters = [
            ["A", "B", "C"],
            ["A", "B", "C", "D"],
            ["A", "B", "C"],
            ["A", "B", "C"],
            ["A", "B", "C", "D"],
            ["A", "B", "C"],
            ["A", "B", "C"],
            ["A", "B", "C"],
            ["A", "B", "C"],
            ["A", "B", "C"],
        ]
        expected_option_texts = [
            ["Universal", "Voto libre", "Intransferible"],
            [
                "Instituto Electoral de Tamaulipas (IETAM)",
                "Tribunal Electoral del Estado de Tamaulipas (TRIELTAM)",
                "Fiscalía Especializada en Delitos Electorales de Tamaulipas. (FEDE)",
                "Instituto Nacional Electoral (INE)",
            ],
            [
                "Tribunal Electoral del Estado de Tamaulipas (TRIELTAM)",
                "Fiscalía Especializada en Materia de Delitos Electorales de la FGR (FISEL)",
                "Tribunal Electoral del Poder Judicial de la Federación (TEPJF)",
            ],
            [
                "Tribunal Electoral del Estado de Tamaulipas (TRIELTAM)",
                "Fiscalía Especializada en Materia de Delitos Electorales de la Fiscalía General de la República (FGR)",
                "Fiscalía Especializada en Delitos Electorales de la Fiscalía General de Justicia del Estado de Tamaulipas (FEDE)",
            ],
            [
                "Gobernador.",
                "Alcaldes y Regidurías.",
                "Presidente de la República.",
                "Diputado Local.",
            ],
            [
                "Mecanismos Administrativos.",
                "Mecanismos Jurisdiccionales.",
                "Mecanismos de Procuración de Justicia.",
            ],
            ["El derecho de huelga.", "El voto.", "La consulta popular."],
            ["Personal.", "Libre.", "Secreto."],
            [
                "Proceso Electoral Federal.",
                "Proceso Electoral Local.",
                "Proceso Electoral Concurrente.",
            ],
            ["Actos de Precampaña", "Veda electoral", "Actos de Campaña"],
        ]

        with patch.object(main, "SessionLocal", Session):
            main.seed_questions()

        with Session() as db:
            questions = db.scalars(
                select(main.Question)
                .where(main.Question.module_id == 1)
                .order_by(main.Question.number)
            ).all()

            self.assertEqual(len(questions), 10)
            self.assertEqual([question.text for question in questions], expected_texts)
            self.assertEqual(
                [
                    [option.letter for option in question.options]
                    for question in questions
                ],
                expected_option_letters,
            )
            self.assertEqual(
                [
                    [option.text for option in question.options]
                    for question in questions
                ],
                expected_option_texts,
            )
            self.assertEqual(
                [
                    [
                        option.letter
                        for option in question.options
                        if option.is_correct
                    ]
                    for question in questions
                ],
                expected_correct_letters,
            )


class ModuleTwoQuestionBankTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        main.Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with patch.object(main, "SessionLocal", self.Session):
            main.seed_module2_questions()

    def tearDown(self):
        self.engine.dispose()

    def test_seed_loads_unique_bank_and_correct_answers(self):
        expected_texts = [
            "De conformidad con lo previsto en el artículo 14 ter del Código Penal del Estado de Tamaulipas, el delito es la conducta típica, antijurídica y culpable a la que se atribuye una o varias sanciones penales.",
            "Es el acto u omisión que contraviene las disposiciones legales en materia electoral y que atenta contra la certeza y efectividad del sufragio.",
            "Solicitar votos por paga, promesa de dinero u otra contraprestación durante la campaña electoral, el día de la jornada electoral o en los tres días previos a esta corresponde a un delito electoral. ¿Cuál es el elemento temporal que exige esta descripción?",
            "¿Cuáles de los siguientes delitos electorales admiten prisión preventiva oficiosa?",
            "¿Qué autoridad electoral en materia penal será competente para conocer de un delito electoral cuando existan indicios suficientes de financiamiento indebido de una campaña electoral proveniente de la delincuencia organizada?",
            "¿Cuál es la autoridad electoral competente para conocer de un delito electoral surgido en una elección de alcaldías y diputaciones locales, como el uso de vehículos del ayuntamiento para asistir a actos de campaña?",
            "¿Cuál es la característica del voto que se transgrede cuando una persona pretende votar con una credencial que no le pertenece?",
            "¿Cuál es el principio constitucional que se transgrede cuando se alteran los resultados electorales o se introducen boletas previamente marcadas en favor de algún partido político o candidato?",
            "¿Cuál es el principio que garantiza condiciones de igualdad real y justicia para todos los partidos políticos y candidatos? Este principio busca que ningún participante tenga ventajas indebidas que afecten los resultados de la elección y se transgrede cuando se destinan bienes o servicios públicos en beneficio de un candidato o partido político.",
            "¿De cuántos artículos se compone la Ley General en Materia de Delitos Electorales?",
            "¿Quiénes tienen prohibido asistir a eventos partidistas con uniforme oficial institucional o en vehículos oficiales?",
            "¿Cuáles son las características de los delitos electorales?",
            "¿En qué Ley se encuentran previstos los delitos electorales?",
            "En el procedimiento administrativo sancionador pueden ser sancionados los partidos políticos, precandidatos y candidatos, candidaturas independientes, personas físicas y morales, personas extranjeras y concesionarios de radio y televisión (artículo 422 de la LGIPE).",
            "¿Cuáles son las consecuencias que tiene la comisión de un delito electoral?",
            "¿Cuáles son las consecuencias que tiene la comisión de una falta administrativa en materia electoral?",
            "¿Ante qué autoridad se denuncian los delitos electorales en Tamaulipas?",
            "Los delitos electorales federales y locales se encuentran contenidos en la misma Ley General en Materia de Delitos Electorales.",
            "¿Cuál es la autoridad electoral competente para conocer de un delito electoral que surge en el contexto de una elección de Senadores y Diputados Federales?",
            "¿Cuál es la característica del voto que se transgrede cuando una persona solicita evidencia del sentido del voto, como podría ser mostrar una fotografía de la boleta marcada?",
            "¿Cuál es la característica del voto que se transgrede cuando una persona servidora pública obliga, presiona o amenaza a sus subordinados para que voten por un candidato o partido político en particular?",
            "De acuerdo con la redacción vigente del artículo 7, fracción VII, de la Ley General en Materia de Delitos Electorales, solamente se puede sancionar penalmente a quien solicita votos a cambio de dinero, pero no al ciudadano que vende su voto.",
        ]
        expected_correct_letters = [
            "C", "A", "B", "B", "A", "B", "A", "C", "A",
            "C", "A", "C", "B", "A", "B", "C", "C", "A", "A",
            "B", "B", "A",
        ]

        with self.Session() as db:
            questions = db.scalars(
                select(main.Question)
                .where(main.Question.module_id == 2)
                .order_by(main.Question.number)
            ).all()

            self.assertEqual(len(questions), 22)
            self.assertEqual([question.text for question in questions], expected_texts)
            self.assertEqual(
                len({question.text.strip().casefold() for question in questions}),
                len(questions),
            )
            self.assertEqual(
                [
                    [
                        option.letter
                        for option in question.options
                        if option.is_correct
                    ]
                    for question in questions
                ],
                [[letter] for letter in expected_correct_letters],
            )

    def test_new_attempt_selects_ten_unique_questions_and_resume_preserves_them(self):
        with self.Session() as db:
            user = main.User(
                first_name="Ana",
                paternal_surname="López",
                maternal_surname="Ruiz",
                email="ana-module2@example.org",
                curp="ABCD1234EFGH5678IJ",
                hashed_password="hashed",
            )
            db.add(user)
            db.commit()

            with patch.object(main, "_require_available_module"):
                response = main.start_evaluation(2, db, user)

            selected_ids = response["question_order"]
            evaluation = db.get(main.Evaluation, response["evaluation_id"])
            all_question_ids = set(db.scalars(
                select(main.Question.id)
                .where(main.Question.module_id == 2)
            ).all())

            self.assertEqual(len(selected_ids), 10)
            self.assertEqual(len(set(selected_ids)), 10)
            self.assertTrue(set(selected_ids).issubset(all_question_ids))
            self.assertEqual(len(all_question_ids), 22)
            self.assertEqual(evaluation.total_questions, 10)
            self.assertEqual(
                main.get_evaluation_question_order(db, evaluation),
                selected_ids,
            )

            with patch.object(main, "_require_available_module"):
                resumed = main.start_evaluation(2, db, user)

            self.assertTrue(resumed["resumed"])
            self.assertEqual(resumed["question_order"], selected_ids)

    def create_legacy_22_question_attempt(self, db, answered_count):
        user = main.User(
            first_name="Ana",
            paternal_surname="López",
            maternal_surname="Ruiz",
            email=f"ana-module2-{answered_count}@example.org",
            curp=f"ABCD1234EFGH567{answered_count}J",
            hashed_password="hashed",
        )
        db.add(user)
        db.flush()

        question_ids = db.scalars(
            select(main.Question.id)
            .where(main.Question.module_id == 2)
            .order_by(main.Question.number)
        ).all()
        evaluation = main.Evaluation(
            user_id=user.id,
            module_id=2,
            attempt_number=1,
            started_at=main.datetime.now(main.timezone.utc).replace(tzinfo=None),
            total_questions=22,
            video_completed=True,
            question_order=json.dumps(question_ids),
            active_attempt_key=f"attempt-{answered_count}",
        )
        db.add(evaluation)
        db.flush()

        selected_ids = main.get_evaluation_question_order(db, evaluation)
        for question_id in selected_ids[:answered_count]:
            correct_option = db.scalar(
                select(main.Option)
                .where(
                    main.Option.question_id == question_id,
                    main.Option.is_correct.is_(True),
                )
            )
            db.add(main.Answer(
                evaluation_id=evaluation.id,
                question_id=question_id,
                option_id=correct_option.id,
                is_correct=True,
            ))
        db.commit()
        return user, evaluation, selected_ids

    def test_legacy_22_question_attempt_finishes_with_only_ten_answers(self):
        with self.Session() as db:
            user, evaluation, selected_ids = self.create_legacy_22_question_attempt(
                db,
                answered_count=10,
            )

            with patch.object(main, "_require_available_module"):
                result = main.finish_evaluation(
                    evaluation.id,
                    main.FinishIn(),
                    db,
                    user,
                )

            self.assertEqual(result["total"], 10)
            self.assertEqual(result["correct"], 10)
            self.assertEqual(result["score"], 100)
            self.assertEqual(evaluation.total_questions, 10)
            self.assertEqual(json.loads(evaluation.question_order), selected_ids)

    def test_finish_error_lists_only_unanswered_selected_question_positions(self):
        with self.Session() as db:
            user, evaluation, _ = self.create_legacy_22_question_attempt(
                db,
                answered_count=9,
            )

            with (
                patch.object(main, "_require_available_module"),
                self.assertRaises(main.HTTPException) as raised,
            ):
                main.finish_evaluation(
                    evaluation.id,
                    main.FinishIn(),
                    db,
                    user,
                )

            self.assertEqual(raised.exception.status_code, 400)
            self.assertEqual(
                raised.exception.detail,
                "Debes responder todas las preguntas visibles. "
                "Preguntas pendientes: 10",
            )
            self.assertEqual(evaluation.total_questions, 10)

    def test_correct_seeded_question_texts_updates_only_known_legacy_text(self):
        legacy_text = (
            "De conformidad con lo previsto en el Artículo 14 ter del Código Penal "
            "del Estado de Tamaulipas, es entendido como la conducta típica, "
            "antijuridica y culpable a la que se le atribuyen una o varias "
            "sanciones penales."
        )
        corrected_text = (
            "De conformidad con lo previsto en el artículo 14 ter del Código Penal "
            "del Estado de Tamaulipas, el delito es la conducta típica, "
            "antijurídica y culpable a la que se atribuye una o varias sanciones "
            "penales."
        )

        with self.Session() as db:
            question = db.scalar(
                select(main.Question).where(
                    main.Question.module_id == 2,
                    main.Question.number == 1,
                )
            )
            question.text = legacy_text
            option = db.scalar(
                select(main.Option)
                .join(main.Question, main.Question.id == main.Option.question_id)
                .where(
                    main.Question.module_id == 2,
                    main.Question.number == 5,
                    main.Option.letter == "B",
                )
            )
            option.text = "Fiscalía Especializa en Delitos Electorales de Tamaulipas (FEDE) de la FGJ."
            db.commit()

        with patch.object(main, "SessionLocal", self.Session):
            main.correct_seeded_question_texts()

        with self.Session() as db:
            question = db.scalar(
                select(main.Question).where(
                    main.Question.module_id == 2,
                    main.Question.number == 1,
                )
            )
            self.assertEqual(question.text, corrected_text)
            option = db.scalar(
                select(main.Option)
                .join(main.Question, main.Question.id == main.Option.question_id)
                .where(
                    main.Question.module_id == 2,
                    main.Question.number == 5,
                    main.Option.letter == "B",
                )
            )
            self.assertEqual(
                option.text,
                "Fiscalía Especializada en Delitos Electorales de Tamaulipas (FEDE) de la FGJ.",
            )

class JwtSecretStartupTests(unittest.TestCase):
    def test_startup_rejects_missing_or_short_secret(self):
        with (
            patch.object(main, "SECRET_KEY", ""),
            patch.object(main, "initialize_database") as initialize_database,
            self.assertRaisesRegex(RuntimeError, "SECRET_KEY"),
        ):
            main.startup_event()

        initialize_database.assert_not_called()

    def test_startup_accepts_long_secret(self):
        with (
            patch.object(main, "SECRET_KEY", "s" * 48),
            patch.object(main, "initialize_database") as initialize_database,
        ):
            main.startup_event()

        initialize_database.assert_called_once_with()


class AuthLimitTests(unittest.TestCase):
    def test_login_state_blocks_after_five_failures(self):
        now = main.datetime.now(main.timezone.utc).replace(tzinfo=None)
        state = main.AuthSecurityState(
            scope="login-ip",
            identifier="127.0.0.1",
            failed_attempts=5,
            window_started_at=now,
        )
        db = Mock()
        db.scalar.return_value = state

        with self.assertRaises(main.HTTPException) as raised:
            main.check_auth_security(db, "login-ip", "127.0.0.1")

        self.assertEqual(raised.exception.status_code, 429)

    def test_reset_password_increments_token_version(self):
        user = SimpleNamespace(
            id=7,
            hashed_password="old",
            token_version=2,
        )
        reset_token = SimpleNamespace(
            expires_at=main.datetime.now(main.timezone.utc).replace(tzinfo=None)
            + main.timedelta(minutes=30),
            user_id=7,
        )
        db = Mock()
        db.scalar.return_value = reset_token
        db.get.return_value = user
        data = main.PasswordResetConfirmIn(
            token="t" * 32,
            new_password="NewPassword123",
        )

        with patch.object(main, "hash_password", return_value="new"):
            response = main.reset_password(data, db)

        self.assertEqual(user.token_version, 3)
        self.assertEqual(response["message"], "Tu contraseña se actualizó. Ya puedes iniciar sesión.")


class PublicCertificateVerificationTests(unittest.TestCase):
    def test_verify_certificate_returns_full_stored_folio_and_name(self):
        certificate = SimpleNamespace(
            user_id=7,
            folio="FEDE-2026-0123456789ABCDEFFEDCBA9876543210",
            course_key=main.COURSE_KEY,
            issued_at=main.datetime.now(main.timezone.utc),
            user_name="Jhovan Rodríguez Moreno",
        )
        user = SimpleNamespace(
            municipality_other=None,
            municipality=SimpleNamespace(name="Victoria"),
            sector=SimpleNamespace(name="Fiscalías"),
        )
        db = Mock()
        db.scalar.return_value = certificate
        db.get.return_value = user

        response = main.verify_certificate(certificate.folio, db)

        self.assertEqual(response["folio"], certificate.folio)
        self.assertEqual(response["user_name"], certificate.user_name)
        self.assertEqual(response["municipality"], "Victoria")
        self.assertEqual(response["sector"], "Fiscalías")

    def test_verify_certificate_accepts_display_folio_without_prefix(self):
        certificate = SimpleNamespace(
            user_id=7,
            folio="FEDE-2026-0123456789ABCDEFFEDCBA9876543210",
            course_key=main.COURSE_KEY,
            issued_at=main.datetime.now(main.timezone.utc),
            user_name="Jhovan Rodríguez Moreno",
        )
        user = SimpleNamespace(
            municipality_other=None,
            municipality=SimpleNamespace(name="Victoria"),
            sector=SimpleNamespace(name="Fiscalías"),
        )
        db = Mock()
        db.scalar.side_effect = [None, certificate]
        db.get.return_value = user

        response = main.verify_certificate(
            "0123456789ABCDEFFEDCBA9876543210",
            db,
        )

        self.assertTrue(response["valid"])
        self.assertEqual(response["folio"], certificate.folio)


class VideoSessionTests(unittest.TestCase):
    def test_rejects_unknown_or_immediate_video_session(self):
        evaluation = SimpleNamespace(
            id=24,
            user_id=7,
            module_id=1,
            completed_at=None,
            video_session_nonce="valid-nonce-of-32-characters!!",
            video_started_at=main.datetime.now(main.timezone.utc).replace(tzinfo=None),
        )
        db = Mock()
        db.get.return_value = evaluation
        user = SimpleNamespace(id=7)
        data = main.VideoCompletedIn(
            nonce="x" * 32,
            played_seconds=10,
        )

        with patch.object(main, "_require_available_module"):
            with self.assertRaises(main.HTTPException) as raised:
                main.mark_video_completed(24, data, db, user)

        self.assertEqual(raised.exception.status_code, 400)


class ValidationAndConcurrencyTests(unittest.TestCase):
    def test_register_rejects_short_or_control_character_name(self):
        with self.assertRaises(Exception):
            main.RegisterIn(
                first_name="\n",
                paternal_surname="Apellido",
                maternal_surname="Apellido",
                email="persona@example.org",
                password="Password123",
                curp="ABCD" * 4,
                state_id=1,
                municipality_id=1,
            )

    def test_database_rejects_two_active_evaluations_for_same_user_and_module(self):
        engine = create_engine("sqlite+pysqlite:///:memory:")
        main.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        with Session() as db:
            first = main.Evaluation(
                user_id=7,
                module_id=1,
                attempt_number=1,
                started_at=main.datetime.now(main.timezone.utc),
                total_questions=10,
                active_attempt_key="7:1",
            )
            db.add(first)
            db.commit()

            duplicate = main.Evaluation(
                user_id=7,
                module_id=1,
                attempt_number=1,
                started_at=main.datetime.now(main.timezone.utc),
                total_questions=10,
                active_attempt_key="7:1",
            )
            db.add(duplicate)
            with self.assertRaises(IntegrityError):
                db.commit()

    def test_register_rejects_invalid_catalog_identifiers(self):
        with self.assertRaises(Exception):
            main.RegisterIn(
                first_name="Ana",
                paternal_surname="López",
                maternal_surname="Ríos",
                email="persona@example.org",
                password="Password123",
                curp="ABCD1234EFGH5678IJ",
                state_id=1,
                municipality_id=1,
                sector_id=0,
            )


class EvaluationScoreTests(unittest.TestCase):
    def test_ten_percent_is_not_converted_to_full_credit(self):
        self.assertEqual(main.score_percentage(10), 10)

    def test_failed_attempt_with_ten_percent_does_not_unlock_next_module(self):
        engine = create_engine("sqlite+pysqlite:///:memory:")
        main.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        with Session() as db:
            user = main.User(
                first_name="Ana",
                paternal_surname="López",
                maternal_surname="Ruiz",
                email="ana@example.org",
                curp="ABCD1234EFGH5678IJ",
                hashed_password="hashed",
            )
            db.add(user)
            db.flush()
            db.add(
                main.Evaluation(
                    user_id=user.id,
                    module_id=1,
                    attempt_number=1,
                    started_at=main.datetime.now(main.timezone.utc),
                    completed_at=main.datetime.now(main.timezone.utc),
                    score=10,
                    correct_answers=1,
                    total_questions=10,
                )
            )
            db.commit()

            statuses = main._module_statuses_for_user(db, user.id)

        self.assertEqual(statuses[0]["best_score"], 10)
        self.assertFalse(statuses[0]["passed"])
        self.assertFalse(statuses[1]["available"])

    def test_score_is_derived_from_answer_counts_when_available(self):
        evaluation = SimpleNamespace(
            score=100,
            correct_answers=1,
            total_questions=10,
        )

        self.assertEqual(main.evaluation_percentage(evaluation), 10)



if __name__ == "__main__":
    unittest.main()
