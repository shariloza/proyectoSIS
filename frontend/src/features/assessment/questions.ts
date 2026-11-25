import type { StudentProfile } from "../../api/client";

type Option<K extends keyof StudentProfile> = { value: StudentProfile[K]; label: string };

/** Textos en español para los valores que acepta la API (tipados contra el contrato OpenAPI). */
export const GENDER: Option<"gender">[] = [
  { value: "Female", label: "Mujer" },
  { value: "Male", label: "Hombre" },
];

export const SLEEP: Option<"sleep_duration">[] = [
  { value: "Less than 5 hours", label: "Menos de 5 horas" },
  { value: "5-6 hours", label: "5 a 6 horas" },
  { value: "7-8 hours", label: "7 a 8 horas" },
  { value: "More than 8 hours", label: "Más de 8 horas" },
];

export const DIET: Option<"dietary_habits">[] = [
  { value: "Healthy", label: "Saludable" },
  { value: "Moderate", label: "Moderada" },
  { value: "Unhealthy", label: "Poco saludable" },
];

export const EDUCATION: Option<"education_level">[] = [
  { value: "secondary", label: "Secundaria / preuniversitario" },
  { value: "undergraduate", label: "Pregrado (licenciatura, ingeniería…)" },
  { value: "postgraduate", label: "Posgrado (maestría, especialidad…)" },
  { value: "doctorate", label: "Doctorado" },
  { value: "other", label: "Otro" },
];

export const FAMILY_HISTORY: Option<"family_history">[] = [
  { value: "No", label: "No" },
  { value: "Yes", label: "Sí" },
];

export const SCALES = [
  {
    name: "academic_pressure",
    label: "¿Cuánta presión académica sientes?",
    low: "Muy poca",
    high: "Muchísima",
  },
  {
    name: "study_satisfaction",
    label: "¿Qué tan satisfecho/a estás con tus estudios?",
    low: "Nada",
    high: "Totalmente",
  },
  {
    name: "financial_stress",
    label: "¿Cuánto estrés te generan tus finanzas?",
    low: "Ninguno",
    high: "Muchísimo",
  },
] as const satisfies readonly { name: keyof StudentProfile; label: string; low: string; high: string }[];

export const INITIAL_PROFILE: StudentProfile = {
  gender: "Female",
  age: 21,
  grade_point_average: 7.5,
  academic_pressure: 3,
  study_satisfaction: 3,
  work_study_hours: 6,
  financial_stress: 3,
  sleep_duration: "7-8 hours",
  dietary_habits: "Moderate",
  education_level: "undergraduate",
  family_history: "No",
};
