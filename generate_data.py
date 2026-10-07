"""Simulação DMAIC com dados 100% fictícios (seed fixa, reprodutível)."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
REV = ["Revenda A", "Revenda B", "Revenda C", "Revenda D"]
MOTIVOS = ["Saída tardia do CD", "Coordenada errada", "Trânsito/obra", "Cliente fechado", "Falta de produto", "Erro de roteirização"]
P_MOT = [0.30, 0.24, 0.16, 0.12, 0.10, 0.08]
PRODS = [f"SKU-{i:02d}" for i in range(1, 21)]
P_PROD = np.array([0.22, 0.17, 0.12, 0.09, 0.07, 0.06, 0.05, 0.04, 0.03, 0.03] + [0.012] * 10)
P_PROD /= P_PROD.sum()


def periodo(n_dias, p_ot, p_if, disp_km_mu, falta_mult=1.0, saida_mult=1.0):
    n = n_dias * 4 * 12  # 12 mapas/revenda/dia
    df = pd.DataFrame({
        "revenda": rng.choice(REV, n),
        "dia_semana": rng.integers(0, 6, n),
        "ot": rng.random(n) < p_ot,
        "if_": rng.random(n) < p_if,
        "km_prev": rng.normal(120, 25, n).clip(40),
    })
    df["km_real"] = df.km_prev + rng.normal(disp_km_mu, 12, n)
    df["disp_km_pct"] = (df.km_real - df.km_prev) / df.km_prev * 100
    df["otif"] = df.ot & df.if_
    return df


antes = periodo(90, 0.82, 0.93, 14)
depois = periodo(90, 0.91, 0.965, 4)

res = {}
for nome, d in [("antes", antes), ("depois", depois)]:
    res[nome] = {
        "OT": d.ot.mean() * 100,
        "IF": d.if_.mean() * 100,
        "OTIF": d.otif.mean() * 100,
        "disp_km_pct": d.disp_km_pct.mean(),
    }
print(pd.DataFrame(res).round(1))

# Pareto de motivos de atraso (período "antes")
atrasos = antes.loc[~antes.ot]
motivos_arr = rng.choice(MOTIVOS, len(atrasos), p=P_MOT)
mot = pd.Series(motivos_arr).value_counts()
par_mot = pd.DataFrame({"qtd": mot, "pct": mot / mot.sum() * 100})
par_mot["acum"] = par_mot.pct.cumsum()
print(par_mot.round(1))

# Pareto de falta por SKU
faltas_arr = rng.choice(PRODS, 3000, p=P_PROD)
faltas = pd.Series(faltas_arr).value_counts()
par_sku = pd.DataFrame({"qtd": faltas, "pct": faltas / faltas.sum() * 100})
par_sku["acum"] = par_sku.pct.cumsum()
print(par_sku.head(6).round(1))
print("SKUs p/ 80%:", int((par_sku.acum < 80).sum() + 1), "de", len(par_sku))

# OTIF por revenda antes/depois
print(pd.DataFrame({
    "antes": antes.groupby("revenda").otif.mean() * 100,
    "depois": depois.groupby("revenda").otif.mean() * 100,
}).round(1))
print("mapas por periodo:", len(antes), len(depois))

antes.loc[atrasos.index, "motivo_atraso"] = motivos_arr
pd.DataFrame({"sku": faltas_arr}).to_csv("faltas_sku.csv", index=False)
antes.assign(periodo="antes").pipe(lambda a: pd.concat([a, depois.assign(periodo="depois")])).to_csv(
    "entregas.csv", index=False)
