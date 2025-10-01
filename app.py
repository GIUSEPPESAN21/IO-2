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
    prob = pulp.LpProblem("ProgramacionPorMetas", pulp.LpMinimize)

    x = pulp.LpVariable.dicts("x", range(1, num_vars + 1), lowBound=0, cat='Continuous')
    d_plus = pulp.LpVariable.dicts("d_plus", range(1, num_goals + 1), lowBound=0, cat='Continuous')
    d_minus = pulp.LpVariable.dicts("d_minus", range(1, num_goals + 1), lowBound=0, cat='Continuous')

    obj_func = pulp.lpSum(
        obj_weights[i-1]['minus'] * d_minus[i] + obj_weights[i-1]['plus'] * d_plus[i] 
        for i in range(1, num_goals + 1)
    )
    prob += obj_func

    for i, goal in enumerate(goals, 1):
        expression = pulp.lpSum(goal['coeffs'][j-1] * x[j] for j in range(1, num_vars + 1))
        prob += expression + d_minus[i] - d_plus[i] == goal['rhs'], f"Meta_{goal.get('name', i)}"

    for i, constraint in enumerate(constraints, 1):
        expression = pulp.lpSum(constraint['coeffs'][j-1] * x[j] for j in range(1, num_vars + 1))
        if constraint['type'] == '<=':
            prob += expression <= constraint['rhs'], f"Restriccion_{constraint.get('name', i)}"
        elif constraint['type'] == '>=':
            prob += expression >= constraint['rhs'], f"Restriccion_{constraint.get('name', i)}"
        else: # '=='
            prob += expression == constraint['rhs'], f"Restriccion_{constraint.get('name', i)}"
            
    prob.solve()

    status = pulp.LpStatus[prob.status]
    solution = {f"x_{j}": x[j].varValue for j in range(1, num_vars + 1)}
    deviations = {f"d_{i}^-": d_minus[i].varValue for i in range(1, num_goals + 1)}
    deviations.update({f"d_{i}^+": d_plus[i].varValue for i in range(1, num_goals + 1)})
    obj_value = pulp.value(prob.objective)

    return status, solution, deviations, obj_value

# --- Interfaz de Usuario de Streamlit ---

st.set_page_config(layout="wide", page_title="Solucionador de Programación por Metas")

st.title("️🎯 Solucionador Interactivo de Programación por Metas")
st.markdown("Esta herramienta te ayuda a encontrar una solución de compromiso para problemas con múltiples objetivos en conflicto.")

# --- Entradas del Usuario en la Barra Lateral ---
st.sidebar.title("Configuración del Modelo")
st.sidebar.info("Define aquí la estructura de tu problema.")

example_option = st.sidebar.selectbox(
    "Cargar un ejemplo del libro de Taha:",
    ("Modelo Personalizado", "Ej. 8.2-1: Agencia de Publicidad", "Ej. Admisión Universitaria")
)

# --- Lógica para pre-cargar los datos del ejemplo ---
if 'last_example' not in st.session_state:
    st.session_state.last_example = ""

if example_option != st.session_state.last_example:
    st.session_state.last_example = example_option
    if example_option == "Ej. 8.2-1: Agencia de Publicidad":
        st.session_state.num_vars, st.session_state.num_goals, st.session_state.num_constraints = 2, 2, 2
        st.session_state.var_names = ["Minutos Radio", "Minutos TV"]
        st.session_state.obj_weights = [{'minus': 2.0, 'plus': 0.0}, {'minus': 0.0, 'plus': 1.0}]
        st.session_state.goal_names = ["Exposición", "Presupuesto"]
        st.session_state.goals = [{'coeffs': [4.0, 8.0], 'rhs': 45.0}, {'coeffs': [8.0, 24.0], 'rhs': 100.0}]
        st.session_state.constraint_names = ["Límite Radio", "Límite Personal"]
        st.session_state.constraints = [{'coeffs': [1.0, 0.0], 'type': '<=', 'rhs': 6.0}, {'coeffs': [1.0, 2.0], 'type': '<=', 'rhs': 10.0}]
    elif example_option == "Ej. Admisión Universitaria":
        st.session_state.num_vars, st.session_state.num_goals, st.session_state.num_constraints = 3, 5, 0
        st.session_state.var_names = ["Estudiantes del Estado", "Estudiantes Fuera del Estado", "Estudiantes Internacionales"]
        st.session_state.obj_weights = [{'minus': 1.0, 'plus': 0.0}, {'minus': 1.0, 'plus': 0.0}, {'minus': 1.0, 'plus': 0.0}, {'minus': 1.0, 'plus': 0.0}, {'minus': 1.0, 'plus': 0.0}]
        st.session_state.goal_names = ["Total Estudiantes", "Promedio ACT", "Internacionales", "Ratio Mujeres/Hombres", "Fuera del Estado"]
        st.session_state.goals = [
            {'coeffs': [1.0, 1.0, 1.0], 'rhs': 1200.0}, {'coeffs': [2.0, 1.0, -2.0], 'rhs': 0.0},
            {'coeffs': [-0.1, -0.1, 0.9], 'rhs': 0.0}, {'coeffs': [0.25, 0.1, -0.4], 'rhs': 0.0},
            {'coeffs': [-0.2, 0.8, -0.2], 'rhs': 0.0}]
        st.session_state.constraints = []
    else: # Modelo Personalizado
        # Limpiar para evitar errores si el usuario reduce el número de variables/metas
        keys_to_clear = ['num_vars', 'num_goals', 'num_constraints', 'var_names', 'obj_weights', 'goal_names', 'goals', 'constraint_names', 'constraints']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

# Estructura del problema
num_vars = st.sidebar.number_input("Número de Variables de Decisión", min_value=1, value=st.session_state.get('num_vars', 2))
num_goals = st.sidebar.number_input("Número de Metas", min_value=1, value=st.session_state.get('num_goals', 2))
num_constraints = st.sidebar.number_input("Número de Restricciones Duras", min_value=0, value=st.session_state.get('num_constraints', 0))

st.sidebar.markdown("---")

# --- Contenedores para la definición del modelo ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Definición de Variables")
    var_names = []
    var_names_state = st.session_state.get('var_names', [])
    for j in range(1, num_vars + 1):
        default_name = var_names_state[j-1] if j - 1 < len(var_names_state) else f"Variable {j}"
        name = st.text_input(f"Nombre de $x_{j}$:", value=default_name, key=f"var_name_{j}")
        var_names.append(name)

    with st.expander("1. Definir Función Objetivo (Pesos)"):
        st.markdown("Asigna pesos a las desviaciones no deseadas. Un peso mayor indica más importancia.")
        obj_weights = []
        weights_state = st.session_state.get('obj_weights', [])
        for i in range(1, num_goals + 1):
            cols_w = st.columns(2)
            weight_dict = weights_state[i-1] if i - 1 < len(weights_state) else {}
            default_minus, default_plus = weight_dict.get('minus', 0.0), weight_dict.get('plus', 0.0)
            weight_minus = cols_w[0].number_input(f"Peso para $d_{i}^-$ (faltante)", key=f"w_m_{i}", value=default_minus)
            weight_plus = cols_w[1].number_input(f"Peso para $d_{i}^+$ (exceso)", key=f"w_p_{i}", value=default_plus)
            obj_weights.append({'minus': weight_minus, 'plus': weight_plus})

with col2:
    with st.expander("2. Definir Metas", expanded=True):
        goals = []
        goal_names = []
        goals_state = st.session_state.get('goals', [])
        goal_names_state = st.session_state.get('goal_names', [])
        for i in range(1, num_goals + 1):
            default_goal_name = goal_names_state[i-1] if i - 1 < len(goal_names_state) else f"Meta {i}"
            goal_name = st.text_input(f"Nombre de la Meta {i}:", value=default_goal_name, key=f"goal_name_{i}")
            goal_names.append(goal_name)
            
            cols = st.columns(num_vars + 1)
            coeffs = []
            goal_dict = goals_state[i-1] if i - 1 < len(goals_state) else {}
            default_coeffs = goal_dict.get('coeffs', [0.0]*num_vars)
            
            for j in range(1, num_vars + 1):
                coeff = cols[j-1].number_input(var_names[j-1], key=f"g{i}_c{j}", value=default_coeffs[j-1])
                coeffs.append(coeff)
            
            default_rhs = goal_dict.get('rhs', 0.0)
            rhs = cols[num_vars].number_input("= Valor Meta", key=f"g{i}_rhs", value=default_rhs)
            goals.append({'name': goal_name, 'coeffs': coeffs, 'rhs': rhs})
            st.markdown("---")

    if num_constraints > 0:
        with st.expander("3. Definir Restricciones Duras (Opcional)"):
            constraints = []
            constraint_names = []
            constraints_state = st.session_state.get('constraints', [])
            constraint_names_state = st.session_state.get('constraint_names', [])
            for i in range(1, num_constraints + 1):
                default_const_name = constraint_names_state[i-1] if i-1 < len(constraint_names_state) else f"Restricción {i}"
                const_name = st.text_input(f"Nombre de la Restricción {i}:", value=default_const_name, key=f"const_name_{i}")
                constraint_names.append(const_name)

                cols = st.columns(num_vars + 2)
                coeffs = []
                const_dict = constraints_state[i-1] if i - 1 < len(constraints_state) else {}
                default_c_coeffs = const_dict.get('coeffs', [0.0]*num_vars)
                
                for j in range(1, num_vars + 1):
                    coeff = cols[j-1].number_input(var_names[j-1], key=f"c{i}_c{j}", value=default_c_coeffs[j-1])
                    coeffs.append(coeff)
                
                default_c_type = const_dict.get('type', '<=')
                constraint_type = cols[num_vars].selectbox("Tipo", ["<=", ">=", "=="], key=f"c{i}_type", index=["<=", ">=", "=="].index(default_c_type))
                default_c_rhs = const_dict.get('rhs', 0.0)
                rhs = cols[num_vars + 1].number_input("Valor", key=f"c{i}_rhs", value=default_c_rhs)
                constraints.append({'name': const_name, 'coeffs': coeffs, 'type': constraint_type, 'rhs': rhs})
                st.markdown("---")
    else:
        constraints = []
        constraint_names = []


# --- Botón para Resolver y Mostrar Resultados ---
if st.button("🚀 Resolver Problema", use_container_width=True, type="primary"):
    with st.spinner("Buscando la mejor solución de compromiso..."):
        try:
            status, solution, deviations, obj_value = solve_goal_programming(
                num_vars, num_goals, num_constraints, obj_weights, goals, constraints
            )
            st.header("Resultados de la Optimización")
            
            if status == "Optimal":
                st.success(f"✅ **Solución Óptima Encontrada**")
                res_col1, res_col2 = st.columns([1, 2])
                
                with res_col1:
                    st.subheader("Variables de Decisión")
                    for j, name in enumerate(var_names, 1):
                        st.metric(label=name, value=f"{solution[f'x_{j}']:.4f}")
                        
                with res_col2:
                    st.subheader("Análisis de Metas")
                    for i, name in enumerate(goal_names, 1):
                        d_minus_val, d_plus_val = deviations[f'd_{i}^-'], deviations[f'd_{i}^+']
                        if (obj_weights[i-1]['minus'] > 0 and d_minus_val > 0.0001):
                            st.warning(f"**{name}:** No cumplida (faltaron {d_minus_val:.4f} unidades)")
                        elif (obj_weights[i-1]['plus'] > 0 and d_plus_val > 0.0001):
                            st.warning(f"**{name}:** No cumplida (se excedió por {d_plus_val:.4f} unidades)")
                        else:
                            st.success(f"**{name}:** Cumplida satisfactoriamente.")
                
                with st.expander("Ver valores detallados de las variables de desviación"):
                    dev_cols = st.columns(2)
                    minus_devs = {k: v for k, v in deviations.items() if k.endswith("^-")}
                    plus_devs = {k: v for k, v in deviations.items() if k.endswith("^+")}
                    dev_cols[0].write(minus_devs)
                    dev_cols[1].write(plus_devs)

                st.info(f"**Valor total de la función objetivo (desviaciones ponderadas minimizadas): {obj_value:.4f}**")
            else:
                st.error(f"No se pudo encontrar una solución óptima. Estado: **{status}**")
        except Exception as e:
            st.error(f"Ocurrió un error al resolver el problema: {e}")

