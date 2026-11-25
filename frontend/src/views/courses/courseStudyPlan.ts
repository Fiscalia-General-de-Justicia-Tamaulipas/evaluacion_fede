export type StudyPlanObjective = {
  code: string;
  text: string;
};

export type StudyPlanTopic = {
  title: string;
  subtopics: string[];
  generalObjective: StudyPlanObjective;
  specificObjectives: StudyPlanObjective[];
};

export type StudyPlanModule = {
  title: string;
  topics: StudyPlanTopic[];
};

export const courseStudyPlan: StudyPlanModule[] = [
  {
    title: 'Generalidades del Derecho Electoral',
    topics: [
      {
        title: '1. Introducción',
        subtopics: [
          '1.1. Democracia en México.',
          '1.2. Mecanismos de protección de la democracia en México.',
          '1.3. El voto como herramienta fundamental para el ejercicio de la democracia.',
        ],
        generalObjective: {
          code: '1.',
          text: 'Definir el concepto de democracia en México, así como la evolución de los mecanismos de protección de la función pública electoral.',
        },
        specificObjectives: [
          {
            code: '1.1.',
            text: 'Exponer el concepto de democracia en México y la importancia de su protección en el sistema jurídico mexicano.',
          },
          {
            code: '1.2.',
            text: 'Dar a conocer los principales mecanismos de protección de la función pública electoral.',
          },
          {
            code: '1.3.',
            text: 'Comentar la importancia del voto y sus características.',
          },
        ],
      },
      {
        title: '2. Proceso Electoral',
        subtopics: [
          '2.1. Concepto de proceso electoral.',
          '2.2. Tipos de proceso electoral.',
          '2.3. Etapas del proceso electoral local.',
          '2.3.1. Etapas del proceso electoral federal.',
          '2.4. Sujetos que intervienen en el proceso electoral: autoridades electorales, funcionarios electorales, funcionarios de casilla y funcionarios de partidos políticos.',
        ],
        generalObjective: {
          code: '2.1.',
          text: 'Plantear las generalidades de los procesos electorales federales y locales, las etapas que los conforman y las atribuciones y facultades de los funcionarios electorales.',
        },
        specificObjectives: [
          {
            code: '2.1.',
            text: 'Que el público participante identifique las etapas de un proceso electoral.',
          },
          {
            code: '2.2.',
            text: 'Presentar las similitudes y diferencias entre los procesos electorales federales y locales.',
          },
          {
            code: '2.3.',
            text: 'Comentar las etapas que conforman un proceso electoral ordinario.',
          },
          {
            code: '2.4.',
            text: 'Que las personas servidoras públicas conozcan las funciones que realizan los sujetos que intervienen en el proceso electoral.',
          },
        ],
      },
      {
        title: '3. Autoridades Electorales',
        subtopics: [
          '3.1. Autoridades administrativas.',
          '3.2. Autoridades jurisdiccionales.',
          '3.3. Autoridades de procuración de justicia.',
        ],
        generalObjective: {
          code: '3.1.',
          text: 'Dar a conocer las atribuciones de las autoridades electorales.',
        },
        specificObjectives: [
          {
            code: '3.1.',
            text: 'Definir las atribuciones del Tribunal Electoral del Estado.',
          },
          {
            code: '3.2.',
            text: 'Dar a conocer las atribuciones de las autoridades administrativas.',
          },
          {
            code: '3.3.',
            text: 'Comentar las principales atribuciones de la Fiscalía Especializada en Delitos Electorales de la Fiscalía General de Justicia del Estado de Tamaulipas.',
          },
        ],
      },
    ],
  },
  {
    title: 'Análisis de los Delitos Electorales',
    topics: [
      {
        title: '4. Concepto de Delito',
        subtopics: [
          '4.1. Concepto de delito desde la teoría causal.',
          '4.2. Concepto de delito conforme al Código Penal del Estado de Tamaulipas (elementos de la tipicidad).',
        ],
        generalObjective: {
          code: '4.1.',
          text: 'Plantear el concepto de delito con base en las teorías más conocidas en el sistema jurídico mexicano.',
        },
        specificObjectives: [
          {
            code: '4.1.',
            text: 'Explicar las generalidades de la teoría del delito.',
          },
          {
            code: '4.2.',
            text: 'Reflexionar sobre los elementos de la tipicidad con base en el numeral 14 del Código Penal del Estado de Tamaulipas.',
          },
        ],
      },
      {
        title: '5. Delitos Electorales',
        subtopics: [
          '5.1. Concepto de delito electoral.',
          '5.2. Características de los delitos electorales.',
          '5.3. Quiénes pueden cometer delitos electorales.',
          '5.4. Delitos electorales federales.',
          '5.5. Delitos electorales locales.',
          '5.6. Delitos electorales más denunciados a nivel local.',
          '5.7. Delitos electorales cometidos por servidores públicos.',
          '5.8. Delitos electorales de prisión preventiva oficiosa.',
          '5.9. Delitos electorales e infracciones administrativas (diferencias).',
        ],
        generalObjective: {
          code: '5.1.',
          text: 'Enseñar las principales conductas que pueden configurar la comisión de delitos electorales en el contexto de un proceso electoral, con el propósito de identificarlas.',
        },
        specificObjectives: [
          {
            code: '5.1.',
            text: 'Dar a conocer la naturaleza jurídica de la Ley General en Materia de Delitos Electorales y el concepto de delito electoral.',
          },
          {
            code: '5.2.',
            text: 'Que las personas servidoras públicas identifiquen las características de los delitos electorales.',
          },
          {
            code: '5.3.',
            text: 'Explicar quiénes pueden cometer delitos electorales.',
          },
          {
            code: '5.4.',
            text: 'Identificar los delitos electorales en una elección federal y sus diferencias y similitudes con los delitos electorales en elecciones locales.',
          },
          {
            code: '5.5.',
            text: 'Que el público participante conozca los delitos electorales que son competencia del Estado de Tamaulipas.',
          },
          {
            code: '5.6.',
            text: 'Ejemplificar los delitos electorales más comunes en el Estado de Tamaulipas.',
          },
          {
            code: '5.7.',
            text: 'Establecer las conductas delictivas en materia electoral que pueden cometer las personas servidoras públicas federales y locales.',
          },
          {
            code: '5.8.',
            text: 'Identificar los delitos electorales que ameritan la imposición de prisión preventiva oficiosa durante la etapa de investigación.',
          },
          {
            code: '5.9.',
            text: 'Explicar las generalidades de las infracciones administrativas electorales, así como sus diferencias y similitudes con los delitos electorales.',
          },
        ],
      },
    ],
  },
  {
    title: 'Integración de la Carpeta de Investigación, Primer Respondiente, Retos en la Investigación y Cultura de Prevención del Delito',
    topics: [
      {
        title: '6. Mecanismos de denuncia',
        subtopics: [
          '6.1. Presencial, mediante comparecencia o presentación directa de escrito.',
          '6.2. Puesta a disposición de persona detenida (flagrancia).',
          '6.3. Generalidades del Informe Policial Homologado.',
          '6.4. Registro Nacional de Detenciones.',
        ],
        generalObjective: {
          code: '6.1.',
          text: 'Presentar al público participante las formas de inicio de la investigación y los mecanismos de denuncia de los delitos electorales.',
        },
        specificObjectives: [
          {
            code: '6.1.',
            text: 'Dar a conocer los requisitos para presentar una denuncia directamente, por comparecencia o mediante escrito.',
          },
          {
            code: '6.2.',
            text: 'Comentar la forma de inicio de una investigación mediante la puesta a disposición de una persona detenida.',
          },
          {
            code: '6.3.',
            text: 'Dar a conocer la importancia del correcto registro del Informe Policial Homologado.',
          },
          {
            code: '6.4.',
            text: 'Comentar acerca del Registro Nacional de Detenciones.',
          },
        ],
      },
      {
        title: '7. Integración de la Carpeta de Investigación',
        subtopics: [
          '7.1. Acuerdo de inicio.',
          '7.2. Orden de investigación.',
          '7.3. Realización de actos de investigación.',
          '7.4. Solicitud y recolección de dictámenes periciales.',
          '7.5. Obtención de datos de prueba.',
        ],
        generalObjective: {
          code: '7.1.',
          text: 'Explicar las generalidades de las principales actuaciones que se realizan al integrar carpetas de investigación en materia electoral.',
        },
        specificObjectives: [
          {
            code: '7.1.',
            text: 'Explicar la forma en que la autoridad ministerial inicia una investigación en materia de delitos electorales.',
          },
          {
            code: '7.2.',
            text: 'Exponer cómo los y las agentes del Ministerio Público especializados en delitos electorales coordinan la investigación.',
          },
          {
            code: '7.3.',
            text: 'Presentar los actos de investigación que pueden realizar los agentes de la Policía de Investigación al integrar una carpeta de investigación por delito electoral.',
          },
          {
            code: '7.4.',
            text: 'Reflexionar sobre los principales dictámenes periciales que los agentes del Ministerio Público pueden recabar al integrar carpetas de investigación en materia de delitos electorales.',
          },
          {
            code: '7.5.',
            text: 'Comentar los niveles de convicción relacionados con los datos de prueba y su diferencia con el concepto de prueba, en el contexto del sistema penal acusatorio.',
          },
        ],
      },
      {
        title: '8. Etapas del Proceso Penal Acusatorio',
        subtopics: [
          '8.1. Etapa inicial.',
          '8.2. Etapa intermedia.',
          '8.3. Juicio oral.',
        ],
        generalObjective: {
          code: '8.1.',
          text: 'Explicar las generalidades de las etapas que conforman el proceso penal acusatorio.',
        },
        specificObjectives: [
          {
            code: '8.1.',
            text: 'Comentar los momentos procesales que conforman la etapa inicial de la investigación.',
          },
          {
            code: '8.2.',
            text: 'Desarrollar las actuaciones de las partes en la etapa intermedia del proceso penal acusatorio.',
          },
          {
            code: '8.3.',
            text: 'Dar a conocer cómo se desarrolla un juicio oral ante la posible comisión de delitos electorales.',
          },
        ],
      },
      {
        title: '9. Retos en la Integración de la Carpeta de Investigación',
        subtopics: [
          '9.1. Anonimato en la presentación de las denuncias.',
          '9.2. Información incompleta en las denuncias de carácter anónimo.',
          '9.3. Recepción de denuncias fuera de tiempo.',
          '9.4. Falta de impulso procesal.',
        ],
        generalObjective: {
          code: '9.',
          text: 'Reflexionar sobre los principales retos que enfrenta la autoridad ministerial en la investigación de los delitos electorales.',
        },
        specificObjectives: [
          {
            code: '9.1.',
            text: 'Exponer cómo el anonimato de las denuncias representa un obstáculo para integrar carpetas de investigación por delitos electorales.',
          },
          {
            code: '9.2.',
            text: 'Reflexionar sobre el impacto negativo que tiene la falta de información en las denuncias anónimas para la integración de carpetas de investigación.',
          },
          {
            code: '9.3.',
            text: 'Dar a conocer el impacto negativo que representan las denuncias presentadas fuera de tiempo.',
          },
          {
            code: '9.4.',
            text: 'Comentar el desinterés de las partes en las denuncias de naturaleza penal electoral y su impacto negativo en la integración de las carpetas de investigación.',
          },
        ],
      },
      {
        title: '10. Cultura de la Prevención',
        subtopics: [
          '10.1. Actividades de prevención que realiza la Fiscalía Especializada en Delitos Electorales.',
          '10.1.1. Difusión en redes sociales.',
          '10.1.2. Actividades de campo.',
          '10.1.3. Spots de radio y televisión.',
          '10.2. Actividades interinstitucionales con enfoque de prevención.',
          '10.3. Reflexiones finales.',
        ],
        generalObjective: {
          code: '10.',
          text: 'Dar a conocer la importancia de la prevención en el contexto de la investigación de delitos electorales.',
        },
        specificObjectives: [
          {
            code: '10.1.',
            text: 'Presentar las principales actividades de prevención en materia penal electoral.',
          },
          {
            code: '10.1.1.',
            text: 'Comentar la importancia de difundir material didáctico en materia penal electoral por redes sociales y cómo contribuye a la prevención de los delitos.',
          },
          {
            code: '10.1.2.',
            text: 'Reflexionar sobre la importancia del contacto directo con la ciudadanía y cómo contribuye a fomentar la cultura de prevención y la protección de los derechos políticos y electorales de la ciudadanía.',
          },
          {
            code: '10.1.3.',
            text: 'Enseñar el impacto positivo del uso de las prerrogativas de radio y televisión y su importancia para fomentar el conocimiento de los delitos electorales.',
          },
          {
            code: '10.2.',
            text: 'Dar a conocer las principales actividades de prevención del delito que se realizan en conjunto con otras autoridades electorales.',
          },
        ],
      },
    ],
  },
];
