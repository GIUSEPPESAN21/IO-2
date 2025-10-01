"""
# Solucionador Interactivo de Programación por Metas

Una aplicación web para modelar y resolver problemas de Programación por Metas (Goal Programming).
Basado en los conceptos del Capítulo 8 de "Investigación de Operaciones" de Hamdy A. Taha.
"""

import streamlit as st
import pulp

def solve_goal_programming(num_vars, num_goals, num_constraints, obj_weights, goals, constraints):
    """
    Resuelve el problema de Programación por Metas usando PuLP.
    """
    # 1. Crear el problema
    prob = pulp.LpProblem("ProgramacionPorMetas", pulp.LpMinimize)

    # 2. Crear variables
    # Variables de decisión
    x = pulp.LpVariable.dicts("x", range(1, num_vars + 1), lowBound=0, cat='Continuous')
    
    # Variables de desviación para las metas
    d_plus = pulp.LpVariable.dicts("d_plus", range(1, num_goals + 1), lowBound=0, cat='Continuous')
    d_minus = pulp.LpVariable.dicts("d_minus", range(1, num_goals + 1), lowBound=0, cat='Continuous')

    # 3. Función Objetivo
    # Minimizar la suma ponderada de las desviaciones no deseadas
    obj_func = pulp.lpSum(
        obj_weights[i-1]['minus'] * d_minus[i] + obj_weights[i-1]['plus'] * d_plus[i] 
        for i in range(1, num_goals + 1)
    )
    prob += obj_func

    # 4. Añadir restricciones
    # Metas
    for i, goal in enumerate(goals, 1):
        expression = pulp.lpSum(goal['coeffs'][j-1] * x[j] for j in range(1, num_vars + 1))
        # Cada meta se convierte en una igualdad con variables de desviación
        prob += expression + d_minus[i] - d_plus[i] == goal['rhs'], f"Meta_{i}"

    # Restricciones duras (hard constraints)
    for i, constraint in enumerate(constraints, 1):
        expression = pulp.lpSum(constraint['coeffs'][j-1] * x[j] for j in range(1, num_vars + 1))
        if constraint['type'] == '<=':
            prob += expression <= constraint['rhs'], f"Restriccion_{i}"
        elif constraint['type'] == '>=':
            prob += expression >= constraint['rhs'], f"Restriccion_{i}"
        else: # '=='
            prob += expression == constraint['rhs'], f"Restriccion_{i}"
            
    # 5. Resolver el problema
    prob.solve()

    # 6. Devolver resultados
    status = pulp.LpStatus[prob.status]
    solution = {f"x_{j}": x[j].varValue for j in range(1, num_vars + 1)}
    deviations = {
        f"d_{i}^-": d_minus[i].varValue for i in range(1, num_goals + 1)
    }
    deviations.update({
        f"d_{i}^+": d_plus[i].varValue for i in range(1, num_goals + 1)
    })
    obj_value = pulp.value(prob.objective)

    return status, solution, deviations, obj_value

# --- Interfaz de Usuario de Streamlit ---

st.set_page_config(layout="wide", page_title="Solucionador de Programación por Metas")

st.title("️🎯 Solucionador Interactivo de Programación por Metas")
st.markdown("Esta herramienta te ayuda a encontrar una solución de compromiso para problemas con múltiples objetivos en conflicto.")

# --- Entradas del Usuario en la Barra Lateral ---

st.sidebar.title("Configuración del Modelo")
st.sidebar.info("Define aquí la estructura de tu problema de Programación por Metas.")

# Cargar ejemplo
example_option = st.sidebar.selectbox(
    "Cargar un ejemplo del libro de Taha:",
    ("Modelo Personalizado", "Ej. 8.2-1: Agencia de Publicidad TopAd", "Ej. Admisión Universitaria (Conjunto 8.1a, Prob. 3)")
)

# --- Lógica para pre-cargar los datos del ejemplo ---

if example_option == "Ej. 8.2-1: Agencia de Publicidad TopAd":
    # Datos del ejemplo de la agencia de publicidad
    st.session_state.num_vars = 2
    st.session_state.num_goals = 2
    st.session_state.num_constraints = 2
    st.session_state.obj_weights = [{'minus': 2.0, 'plus': 0.0}, {'minus': 0.0, 'plus': 1.0}]
    st.session_state.goals = [
        {'coeffs': [4.0, 8.0], 'rhs': 45.0},
        {'coeffs': [8.0, 24.0], 'rhs': 100.0}
    ]
    st.session_state.constraints = [
        {'coeffs': [1.0, 0.0], 'type': '<=', 'rhs': 6.0},
        {'coeffs': [1.0, 2.0], 'type': '<=', 'rhs': 10.0}
    ]
elif example_option == "Ej. Admisión Universitaria (Conjunto 8.1a, Prob. 3)":
    # Datos del ejemplo de admisiones
    st.session_state.num_vars = 3
    st.session_state.num_goals = 5
    st.session_state.num_constraints = 0
    # Asumiendo pesos iguales para simplificar
    st.session_state.obj_weights = [
        {'minus': 1.0, 'plus': 0.0}, {'minus': 1.0, 'plus': 0.0},
        {'minus': 1.0, 'plus': 0.0}, {'minus': 1.0, 'plus': 0.0},
        {'minus': 0.0, 'plus': 1.0}
    ]
    st.session_state.goals = [
        {'coeffs': [1.0, 1.0, 1.0], 'rhs': 1200.0}, # Meta 1: >= 1200 estudiantes
        {'coeffs': [2.0, 1.0, -2.0], 'rhs': 0.0},  # Meta 2: >= 25 ACT promedio
        {'coeffs': [-0.1, -0.1, 0.9], 'rhs': 0.0},  # Meta 3: >= 10% internacionales
        {'coeffs': [0.25, 0.1, -0.4], 'rhs': 0.0}, # Meta 4: >= 3:4 mujeres-hombres
        {'coeffs': [-0.2, 0.8, -0.2], 'rhs': 0.0}   # Meta 5: >= 20% fuera del estado
    ]
    st.session_state.constraints = []
else: # Modelo Personalizado
    # Limpiar el estado si se cambia a personalizado
    if 'num_vars' in st.session_state and st.session_state.get('last_example') != "Modelo Personalizado":
        del st.session_state.num_vars
    st.session_state.last_example = "Modelo Personalizado"


# Estructura del problema
num_vars = st.sidebar.number_input("Número de Variables de Decisión ($x_i$)", min_value=1, value=st.session_state.get('num_vars', 2), key='num_vars_input')
num_goals = st.sidebar.number_input("Número de Metas", min_value=1, value=st.session_state.get('num_goals', 2), key='num_goals_input')
num_constraints = st.sidebar.number_input("Número de Restricciones Duras (opcional)", min_value=0, value=st.session_state.get('num_constraints', 0), key='num_constraints_input')

st.sidebar.markdown("---")

# --- Contenedores para la definición del modelo en la página principal ---

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Función Objetivo")
    st.markdown("Define los **pesos** para minimizar las desviaciones no deseadas. Un peso mayor significa mayor importancia. Deja en 0 los pesos de las desviaciones que no te importa minimizar.")
    
    obj_weights = []
    for i in range(1, num_goals + 1):
        cols = st.columns(2)
        default_minus = st.session_state.get('obj_weights', [{} for _ in range(num_goals)])[i-1].get('minus', 0.0)
        default_plus = st.session_state.get('obj_weights', [{} for _ in range(num_goals)])[i-1].get('plus', 0.0)
        
        weight_minus = cols[0].number_input(f"Peso para $d_{i}^-$ (faltante)", key=f"w_m_{i}", value=default_minus)
        weight_plus = cols[1].number_input(f"Peso para $d_{i}^+$ (exceso)", key=f"w_p_{i}", value=default_plus)
        obj_weights.append({'minus': weight_minus, 'plus': weight_plus})

with col2:
    st.subheader("2. Metas")
    st.markdown("Define cada una de tus metas. El solucionador las convertirá a la forma `Expresión + d⁻ - d⁺ = Valor`.")
    
    goals = []
    for i in range(1, num_goals + 1):
        st.markdown(f"**Meta {i}**")
        cols = st.columns(num_vars + 2)
        coeffs = []
        
        default_coeffs = st.session_state.get('goals', [{} for _ in range(num_goals)])[i-1].get('coeffs', [0.0]*num_vars)
        
        for j in range(1, num_vars + 1):
            coeff = cols[j-1].number_input(f"$x_{j}$", key=f"g{i}_c{j}", label_visibility="label", value=default_coeffs[j-1])
            coeffs.append(coeff)
        
        st.write("=") # Todas las metas se convierten en igualdades
        
        default_rhs = st.session_state.get('goals', [{} for _ in range(num_goals)])[i-1].get('rhs', 0.0)
        rhs = cols[num_vars + 1].number_input("Valor", key=f"g{i}_rhs", label_visibility="label", value=default_rhs)
        goals.append({'coeffs': coeffs, 'rhs': rhs})
        st.markdown("---")

if num_constraints > 0:
    with col2:
        st.subheader("3. Restricciones Duras (Opcional)")
        st.markdown("Estas son restricciones que **deben** cumplirse (no son flexibles).")
        
        constraints = []
        for i in range(1, num_constraints + 1):
            st.markdown(f"**Restricción {i}**")
            cols = st.columns(num_vars + 2)
            coeffs = []
            
            default_c_coeffs = st.session_state.get('constraints', [{} for _ in range(num_constraints)])[i-1].get('coeffs', [0.0]*num_vars)
            
            for j in range(1, num_vars + 1):
                coeff = cols[j-1].number_input(f"$x_{j}$", key=f"c{i}_c{j}", label_visibility="label", value=default_c_coeffs[j-1])
                coeffs.append(coeff)
            
            default_c_type = st.session_state.get('constraints', [{} for _ in range(num_constraints)])[i-1].get('type', '<=')
            constraint_type = cols[num_vars].selectbox("Tipo", ["<=", ">=", "=="], key=f"c{i}_type", index=["<=", ">=", "=="].index(default_c_type))

            default_c_rhs = st.session_state.get('constraints', [{} for _ in range(num_constraints)])[i-1].get('rhs', 0.0)
            rhs = cols[num_vars + 1].number_input("Valor", key=f"c{i}_rhs", label_visibility="label", value=default_c_rhs)
            constraints.append({'coeffs': coeffs, 'type': constraint_type, 'rhs': rhs})
            st.markdown("---")
else:
    constraints = []


# --- Botón para Resolver y Mostrar Resultados ---

if st.button("🚀 Resolver Problema", use_container_width=True):
    with st.spinner("Buscando la mejor solución de compromiso..."):
        try:
            status, solution, deviations, obj_value = solve_goal_programming(
                num_vars, num_goals, num_constraints, obj_weights, goals, constraints
            )

            st.header("Resultados de la Optimización")
            
            if status == "Optimal":
                st.success(f"✅ **Solución Óptima Encontrada**")
                
                res_col1, res_col2, res_col3 = st.columns(3)
                
                with res_col1:
                    st.subheader("Valor de las Variables de Decisión")
                    for var, value in solution.items():
                        st.metric(label=f"${var}$", value=f"{value:.4f}")
                        
                with res_col2:
                    st.subheader("Análisis de Metas")
                    for i in range(1, num_goals + 1):
                        d_minus_val = deviations[f'd_{i}^-']
                        d_plus_val = deviations[f'd_{i}^+']
                        
                        if obj_weights[i-1]['minus'] > 0 and d_minus_val > 0:
                            st.warning(f"**Meta {i} NO cumplida:** Faltaron {d_minus_val:.4f} unidades.")
                        elif obj_weights[i-1]['plus'] > 0 and d_plus_val > 0:
                             st.warning(f"**Meta {i} NO cumplida:** Se excedió por {d_plus_val:.4f} unidades.")
                        else:
                            st.success(f"**Meta {i} cumplida** satisfactoriamente.")
                
                with res_col3:
                    st.subheader("Valor de las Variables de Desviación")
                    for var, value in deviations.items():
                        st.text(f"{var} = {value:.4f}")

                st.info(f"**Valor total de la función objetivo (desviaciones ponderadas minimizadas): {obj_value:.4f}**")

            else:
                st.error(f"No se pudo encontrar una solución óptima. Estado: **{status}**")
        except Exception as e:
            st.error(f"Ocurrió un error al resolver el problema: {e}")
