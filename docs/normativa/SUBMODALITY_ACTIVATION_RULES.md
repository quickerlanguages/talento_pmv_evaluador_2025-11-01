---

# SUBMODALITY ACTIVATION RULES
## Proyecto Talento

**Versión:** 1.1  
**Estado:** Vigente  
**Carácter:** Vinculante (proceso de activación) + Normativo interpretativo (Anexo A)  
**Ámbito:** Exclusivo para EVAL  
**Referencia normativa:** EVAL_CORE_v1_1

---

## 1. Propósito

Este documento define el **procedimiento formal y obligatorio** para proponer, evaluar y decidir la **activación normativa** de una submodalidad en el modo **EVAL**, preservando:
- pureza de medición (una CCP dominante por ítem EVAL),
- estabilidad métrica,
- y comparabilidad histórica.

Este documento incluye un **anexo normativo interpretativo** (Anexo A) que debe consultarse obligatoriamente en toda propuesta.

Este procedimiento es complementario y subordinado a EVAL_CORE_v1_1, sin redefinir submodalidades ni CCP.

---

## 2. Procedimiento de Activación de Submodalidad (plantilla)

**Submodalidad:** <codigo>  
**Propuesta:** active | latent | excluded  
**Versión objetivo:** EVAL_CORE_vX_Y  
**Autor:** <nombre>  
**Fecha:** <YYYY-MM-DD>

### 2.1 Propósito y señal nueva
- ¿Qué señal aporta esta submodalidad que NO cubren las submodalidades activas actuales?
- ¿Qué CCP dominante pretende aislar en modo EVAL?

### 2.2 Riesgo (matriz)
Evalúa 0–2 cada eje (0=bajo, 1=medio, 2=alto):
- Contaminación CCP:
- Fragilidad métrica:
- Ambigüedad interpretativa:
- Potencial “caballo de Troya”:

**Riesgo total (0–8):** <n>  
**Clasificación:** 🟢 (0–2) / 🟡 (3–5) / 🔴 (6–8)

**Consulta obligatoria:** justificar la clasificación usando el **Anexo A — Mapa de Riesgo por Submodalidad**.

### 2.3 Especificación EVAL permitida
- Diseño mínimo del ítem (sin aprendizaje; sin feedback correctivo; sin cambio de regla salvo FM; sin mezcla relevante de CCP).
- Parámetros de dificultad declarados (lista exhaustiva y gobernada).
- Exclusiones explícitas (qué NO se permite para seguir siendo EVAL).

### 2.4 Reglas de control de deriva
- Límite de duración (si aplica).
- Restricciones de contenido (si aplica: vocabulario/campo semántico/control cultural).
- Reglas anti-entrenamiento implícito (p. ej., evitar patrones repetibles o cambios predecibles).

### 2.5 Impacto en comparabilidad histórica
- ¿Rompe comparabilidad con datos previos? (sí/no)
- Si sí: especificar si requiere **bump major** (EVAL_CORE_vX_0 → v(X+1)_0) o basta **bump minor** (vX_Y → vX_(Y+1)).

### 2.6 Plan de validación
- Métricas esperadas (qué debe correlacionar y qué NO).
- Prueba de contaminación (checklist de exclusiones y pruebas negativas).
- Tamaño mínimo de muestra / sesiones.

### 2.7 Decisión normativa
- Estado final: active | latent | excluded
- `introduced_in_version`: EVAL_CORE_vX_Y
- Notas normativas obligatorias (restricciones, exclusiones y parámetros críticos).

---

## Anexos normativos

---

## Anexo A — Mapa de Riesgo por Submodalidad

**Carácter:** Normativo interpretativo  
**Función:** Instrumento de apoyo obligatorio a decisiones de activación  
**Ámbito:** Exclusivo para EVAL  

Este anexo clasifica las submodalidades cognitivas según su nivel de riesgo
para la evaluación EVAL, con el fin de prevenir contaminación de capacidades
cognitivas primarias (CCP), fragilidad métrica y rupturas de comparabilidad
histórica.

La presente clasificación **no activa ni desactiva submodalidades por sí misma**,
pero **debe ser consultada obligatoriamente** en cualquier propuesta formal de
activación de una submodalidad latente.

---

## 1. Criterios de riesgo utilizados

Cada submodalidad se evalúa según los siguientes ejes normativos:

1. **Riesgo de contaminación CCP**  
   Probabilidad de activar capacidades cognitivas primarias no deseadas en modo EVAL.

2. **Fragilidad métrica**  
   Sensibilidad excesiva a aprendizaje implícito, estrategias, contexto o dependencia
   de hardware.

3. **Ambigüedad interpretativa**  
   Dificultad para interpretar los resultados sin inferencias externas o juicios no
   controlados.

4. **Potencial de “caballo de Troya”**  
   Capacidad de introducir de forma no explícita FM, INH, MDT u otras CCP bajo una
   apariencia funcional simple.

Clasificación de riesgo resultante:
- 🟢 **Bajo riesgo**
- 🟡 **Riesgo medio**
- 🔴 **Alto riesgo / Caballo de Troya**

---

## 2. Submodalidades de bajo riesgo (núcleo seguro)

Estas submodalidades constituyen el **núcleo evaluativo más estable** y deben ser
siempre el punto de partida del sistema EVAL.

### 🟢 Visual simple — estímulo único / reacción

- **CCP objetivo:** VPM  
- **Riesgos:** mínimos  
- **Comentario normativo:**  
  Submodalidad ejemplar: limpia, estable y poco entrenable durante la ejecución.  
- **Estado recomendado:** Activa

---

### 🟢 Búsqueda visual estática controlada

- **CCP objetivo:** ATN (selectiva)  
- **Riesgos:** bajos, siempre que se evite memoria y cambio de reglas  
- **Punto crítico:**  
  La introducción de secuencias o repetición activa MDT.  
- **Estado recomendado:** Activa, con parámetros estrictos

---

### 🟢 Secuencias homogéneas FIFO

- **CCP objetivo:** MCP  
- **Riesgos:** bajos  
- **Comentario normativo:**  
  En el momento en que aparece transformación, deja de ser MCP.  
- **Estado recomendado:** Activa

---

## 3. Submodalidades de riesgo medio (frágiles pero útiles)

Estas submodalidades pueden utilizarse en EVAL, pero requieren **control normativo
estricto** y expansión deliberadamente lenta.

### 🟡 Matrices visuales complejas

- **CCP objetivo:** ABS  
- **Riesgos:**  
  - activación secundaria de MDT,  
  - estrategias aprendidas,  
  - efecto de familiaridad (“he visto esto antes”).  
- **Medidas de contención:**  
  limitar complejidad, evitar patrones culturales, rotar familias de ítems.  
- **Estado recomendado:** Activa con restricciones severas

---

### 🟡 Flexibilidad por cambio de regla explícito

- **CCP objetivo:** FM  
- **Riesgos:**  
  - cambio predecible → entrenamiento implícito,  
  - cambio abrupto → carga inhibitoria.  
- **Comentario normativo:**  
  La FM es inherentemente inestable, pero funcionalmente inevitable.  
- **Estado recomendado:** Activa mínima (v1), expansión lenta

---

### 🟡 Decisión A/B semántica ligera

- **CCP objetivo:** VPM decisional o ABS ligera  
- **Riesgos:**  
  - carga cultural,  
  - inferencias verbales no controladas.  
- **Regla normativa:**  
  Cuando el significado importa más que la forma, la submodalidad queda fuera de EVAL.  
- **Estado recomendado:** Latente prolongado

---

## 4. Submodalidades de alto riesgo (caballos de Troya)

Estas submodalidades tienden a **romper la pureza del sistema evaluativo** y no deben
activarse en EVAL sin una redefinición mayor del marco.

### 🔴 Stroop y derivados

- **Apariencia funcional:** INH  
- **Realidad cognitiva:** INH + FM + lectura automática + aprendizaje estratégico  
- **Riesgo:** extremo  
- **Comentario normativo:**  
  Stroop no mide lo que aparenta medir en un sistema EVAL limpio.  
- **Estado recomendado:** Excluida de EVAL (permitida en TRAIN o evaluación externa)

---

### 🔴 Dual-task (doble tarea)

- **Apariencia funcional:** ATN dividida  
- **Realidad cognitiva:** MDT + FM + gestión estratégica  
- **Riesgo:** extremo  
- **Comentario normativo:**  
  La atención dividida no es una CCP aislable en evaluación digital limpia.  
- **Estado recomendado:** Latente indefinida / probablemente excluida

---

### 🔴 Auditiva secuencial (estado actual)

- **Apariencia funcional:** MCP / ATN  
- **Realidad cognitiva:**  
  dependencia de hardware, contexto acústico y ruido ambiental  
- **Riesgo:** técnico y cognitivo  
- **Estado recomendado:** Latente estratégica (fase futura)

---

### 🔴 Tareas “ecológicas” o gamificadas

- **Apariencia funcional:** realismo  
- **Realidad cognitiva:** mezcla masiva de CCP + motivación + PDE  
- **Riesgo:** máximo  
- **Comentario normativo:**  
  Excelentes para TRAIN; incompatibles con EVAL.  
- **Estado recomendado:** Prohibidas en EVAL

---

## 5. Submodalidades especialmente traicioneras

Estas configuraciones presentan riesgos transversales incluso cuando se aplican a
submodalidades en principio aceptables.

- **Repetición con feedback implícito**  
  Activa aprendizaje no declarado y rompe métricas longitudinales.

- **Ritmos adaptativos automáticos**  
  Contaminan dificultad y destruyen comparabilidad histórica.

- **Atención sostenida excesivamente prolongada**  
  Introduce fatiga, motivación y PDE, convirtiendo ATN en prueba de resistencia.

---

## 6. Reglas estratégicas de oro

1. Si una submodalidad requiere una explicación extensa, no es EVAL.  
2. Si el usuario mejora durante la ejecución, no es EVAL.  
3. Si dos expertos no interpretan igual el resultado, no es EVAL.  
4. Si parece “más realista”, probablemente pertenece a TRAIN.

---

## 7. Recomendación ejecutiva para EVAL_CORE_v1_1

- Mantener un núcleo EVAL pequeño y limpio.  
- Activar submodalidades únicamente cuando:
  - aporten señal cognitiva nueva,
  - no erosionen perfiles existentes,
  - y no obliguen a reinterpretar datos históricos.

---

### Cláusula final

La clasificación de riesgo no constituye un juicio pedagógico, clínico ni moral.
Es una evaluación normativa orientada exclusivamente a preservar la integridad,
estabilidad y comparabilidad del sistema EVAL.

Este documento constituye el marco operativo definitivo para la gobernanza de submodalidades en EVAL_CORE_v1_1 y versiones minor sucesivas, salvo redefinición explícita en versión major.

---

## Anexo B — Tabla Canónica de Submodalidades (estado EVAL_CORE_v1_1) (síntesis ejecutiva)

| ID | Submodalidad        | Uso actual (items) | Estado recomendado (v1_1) | Riesgo | CCP típicas                       | Notas / regla de oro |
|----|--------------------|--------------------|----------------------------|--------|-----------------------------------|----------------------|
| 1  | motriz             | 2                  | active                     | 🟢 bajo | VPM (ejecutiva), INH (Go/No-Go)   | Estable si la regla es fija; cuidado con combinaciones que introduzcan FM |
| 2  | visual             | 4                  | active                     | 🟢 bajo | VPM (sensorial), MDT visual simple | “Visual simple” es limpio; si hay transformación → MDT/ABS |
| 3  | auditiva           | 0                  | latent                     | 🔴 alto | MCP / ATN (teóricas)              | Dependiente de hardware y contexto; posponer a fase futura |
| 4  | vigilancia         | 1                  | active (con límites)        | 🟡 medio | ATN sostenida (CPT)               | Controlar duración; evitar fatiga, PDE y bloques largos |
| 5  | busqueda_visual    | 1                  | active                     | 🟢 bajo | ATN selectiva                     | Evitar repetición o secuencias que activen MDT |
| 6  | cambio_regla       | 2                  | active (mínimo)             | 🟡 medio | FM                                | Cambio predecible = TRAIN implícito; declarar frecuencia |
| 7  | matriz_no_verbal   | 2                  | active (restringida)        | 🟡 medio | ABS                               | Riesgo de MDT/estrategia; rotar familias y controlar patrones |
| 8  | analogia_simple    | 1                  | latent prolongado           | 🟡→🔴   | ABS ligera                        | Riesgo cultural/verbal; si el significado pesa más que la forma → fuera de EVAL |