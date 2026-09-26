export type PipelineStep = {
  id: string;
  n: string;
  name: string;
  tagline: string;
  input: string;
  output: string;
  accent: string;
};

export const PIPELINE: PipelineStep[] = [
  {
    id: "researcher",
    n: "01",
    name: "Researcher",
    tagline: "Mapea tu cuadra como un detective",
    input: "Rubro + zona",
    output: "Encuentra unos 12 locales de tu zona con sus puntajes, opiniones, horarios y fotos. Sin repetidos, sin humo.",
    accent: "#FF5C00",
  },
  {
    id: "analyst",
    n: "02",
    name: "Analyst",
    tagline: "Lee 400 opiniones por vos",
    input: "Reviews crudas",
    output: "Lee cientos de opiniones y junta las quejas y los elogios que se repiten: si te matan las esperas o si aman tu flat white, lo ves acá.",
    accent: "#FF8A3D",
  },
  {
    id: "strategist",
    n: "03",
    name: "Strategist",
    tagline: "Encuentra el hueco que nadie ve",
    input: "Datos ordenados",
    output: "Hueco concreto: “0/40 opiniones hablan de la merienda de tarde” → oportunidad de alta confianza.",
    accent: "#FFB25C",
  },
  {
    id: "creator",
    n: "04",
    name: "Creator",
    tagline: "Diseña el post con tu marca",
    input: "Hueco + tu marca",
    output: "Texto + hashtags + imagen con tus colores y tono barrial. Listo en 5 minutos.",
    accent: "#FF5C00",
  },
  {
    id: "publisher",
    n: "05",
    name: "Publisher",
    tagline: "Vos aprobás, él publica",
    input: "Borrador",
    output: "El post queda listo y vos lo aprobás con un clic. Si querés, se programa solo en tu Instagram.",
    accent: "#FFD9A3",
  },
];

export type UseCase = {
  id: string;
  rubro: string;
  negocio: string;
  zona: string;
  quote: string;
  dueno: string;
  problema: string;
  hallazgo: string;
  accion: string;
  metricas: { label: string; antes: string; despues: string; delta: string }[];
  color: string;
};

export const USE_CASES: UseCase[] = [
  {
    id: "cafe",
    rubro: "Café de especialidad",
    negocio: "Café Ejemplo",
    zona: "Palermo Soho",
    quote: "Pasamos de pelear el mediodía a adueñarnos de la tarde.",
    dueno: "Martina, dueña",
    problema: "Mediodía saturado, tarde muerta. Vecinos con 4.6★ y 842 opiniones.",
    hallazgo: "Nadie hablaba de la merienda de tarde (0/40 opiniones). Y en 2 de 3 vecinos se repetían las quejas por la espera.",
    accion: "Serie “Tarde sin espera”: 3 posts + promo merienda 16–19h con tono cercano y barrial.",
    metricas: [
      { label: "Visitas 16–19h", antes: "18 / día", despues: "31 / día", delta: "+72%" },
      { label: "Rating Google", antes: "4.2★", despues: "4.6★", delta: "+0.4" },
      { label: "Tiempo crear post", antes: "3 horas", despues: "5 min", delta: "-97%" },
    ],
    color: "#FF5C00",
  },
  {
    id: "barberia",
    rubro: "Barbería",
    negocio: "Navaja & Co.",
    zona: "Villa Crespo",
    quote: "Descubrimos que nos mataban los sábados por no responder reseñas.",
    dueno: "Damián, fundador",
    problema: "Sábados vacíos pese a buen corte. Competencia con más reseñas y respuesta activa.",
    hallazgo: "37% de quejas eran por “no contestan mensajes”. Ningún competidor ofrecía reserva por WhatsApp visible.",
    accion: "Post “Reservá tu sábado en 20 segundos” + plantilla de respuesta a reseñas + recordatorio automático.",
    metricas: [
      { label: "Reservas sábado", antes: "9 / día", despues: "21 / día", delta: "+133%" },
      { label: "Reseñas / mes", antes: "6", despues: "28", delta: "+367%" },
      { label: "No-shows", antes: "22%", despues: "8%", delta: "-64%" },
    ],
    color: "#FF8A3D",
  },
  {
    id: "pizzeria",
    rubro: "Pizzería napolitana",
    negocio: "Forno Barrial",
    zona: "Caballito",
    quote: "El delivery nos estaba hundiendo y ni lo sabíamos.",
    dueno: "Lucía y Pablo",
    problema: "Delivery con quejas de frialdad. Salón bien valorado pero invisible en Instagram.",
    hallazgo: "Se repetían las quejas de que la pizza “llega fría”. Y los vecinos publicaban 5 veces por semana contra 1 vez por mes de ellos.",
    accion: "Post “Del horno a tu mesa en 25′ o va por nosotros” + cambio de packaging + calendario de 3 posts/semana.",
    metricas: [
      { label: "Pedidos delivery", antes: "120 / sem", despues: "204 / sem", delta: "+70%" },
      { label: "Quejas frío", antes: "19%", despues: "4%", delta: "-79%" },
      { label: "Alcance IG", antes: "1.2k", despues: "9.8k", delta: "+717%" },
    ],
    color: "#B45309",
  },
];

export const FAQS = [
  {
    q: "¿Esto es legal? ¿Scrapean datos?",
    a: "100% legal. Usamos datos públicos de mapas y reseñas, los mismos que cualquiera puede ver en Google. Nunca tocamos tu cuenta ni publicamos nada sin tu permiso.",
  },
  {
    q: "¿Publica solo sin mi permiso?",
    a: "No. El post queda en borrador y vos lo aprobás o rechazás con un clic. Solo se publica lo que vos autorices, nada más.",
  },
  {
    q: "Soy un negocio chico, ¿me sirve?",
    a: "Es exactamente para vos: cafés, barberías, pizzerías y comercios que no tienen tiempo de monitorear competencia ni agencia de marketing. En 5 minutos tenés la oportunidad detectada + el post.",
  },
  {
    q: "¿Qué necesito para empezar?",
    a: "Solo tu rubro y tu zona. Si querés, sumás los colores, el logo y el tono de tu negocio para que el post salga con tu identidad.",
  },
  {
    q: "¿Cómo sé que la oportunidad es posta?",
    a: "Cada oportunidad viene con su prueba (ej: “18 opiniones hablan de esperas en 2 de 3 competidores”) y un nivel de confianza (alta/media). Ves el porqué, no tenés que creernos de palabra.",
  },
];

export const STATS = [
  { value: 72, suffix: "%", label: "más visitas en horario hueco", prefix: "+" },
  { value: 97, suffix: "%", label: "menos tiempo creando contenido", prefix: "-" },
  { value: 5, suffix: " min", label: "de dato a post listo", prefix: "" },
  { value: 400, suffix: "+", label: "opiniones leídas por zona", prefix: "" },
];
