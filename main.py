import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# --- Dane wejściowe = PM ---
# Pobieramy 50 wierszy pierwszej kolumny z pliku baza.xlsx
path = "baza.xlsx"
df = pd.read_excel(path, header=1, nrows=50)
df.index = df.index + 1
PM = df['PM2.5 [μg/m³]']

# --- Funkcja przynależności (trójkątna) trimf ---
def trimf(x, a, b, c):
    return np.maximum(0, np.minimum((x-a)/(b-a+1e-9), (c-x)/(c-b+1e-9)))

# --- Defuzzyfikacja centroidem ---
def centroid(y, mu):
    if np.sum(mu) == 0: return 0.0
    return np.sum(y * mu) / np.sum(mu)

# --- Fuzyfikacja dla PM ---
# Dla każdego PM sprawdzamy wartość przecięcia dla mu_niskie, mu_srednie i mu_wysokie.
def fuzyfikacja_PM(PM):
    mu_niskie = trimf(PM,-35, 0, 35)
    mu_srednie = trimf(PM, 15, 45, 75)
    mu_wysokie = trimf(PM, 50, 150, 250)
    return mu_niskie, mu_srednie, mu_wysokie

# --- Dane wyjściowe = jakość ---
# Tworzymy 3 typy jakości, tutaj jako przynależności (trimf) używając zmiennej Jakość tablicą z 500 równo oddzielonymi wartościami między 0 a 100.
Jakosc = np.linspace(0, 100, 500)
jakosc_zla = trimf(Jakosc, 0, 0, 50)
jakosc_umiarkowana = trimf(Jakosc, 0, 50, 100)
jakosc_dobra = trimf(Jakosc, 50, 100, 100)

# --- Reguły + Wynik ---
# Używając wartości reguł (wartości fuzyfikacji) oraz typów jakości: Przycinamy każdą jakość o tę wartość (regula*) oraz
# nakładamy na siebie te 3 przycięte trójkąty (trimf), oraz liczymy centroid (defuzyfikacja) jako wartość FIS.
def Wynik(PM):
    mu_niskie, mu_srednie, mu_wysokie = fuzyfikacja_PM(PM)
    regula1 = mu_niskie
    regula2 = mu_srednie
    regula3 = mu_wysokie

    Jakosc_wyjscia = np.maximum.reduce([
        np.minimum(regula1, jakosc_dobra),
        np.minimum(regula2, jakosc_umiarkowana),
        np.minimum(regula3, jakosc_zla),
    ])

    return centroid(Jakosc, Jakosc_wyjscia)

# Do kolumny 'Wynik FIS (do uzupełnienia)' wpisuje odpowiedni Wynik FIS.
df['Wynik FIS (do uzupełnienia)'] = [round(Wynik(pm), 2) for pm in PM]

# --- Wykres funkcji przynależności wejście/wyjście ---
# WYKRES 1: wejście PM2.5
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))
x = np.linspace(0, 150, 500)
mu_n, mu_s, mu_w = fuzyfikacja_PM(x)

ax1.plot(x, mu_n, label='niskie')
ax1.plot(x, mu_s, label='średnie')
ax1.plot(x, mu_w, label='wysokie')
ax1.set_title('Wejście: PM2.5')
ax1.set_xlabel('PM2.5 [μg/m³]')
ax1.set_ylabel('μ')
ax1.legend()
ax1.grid(True)

# WYKRES 2: wyjście jakość
ax2.plot(Jakosc, jakosc_zla, label='zła')
ax2.plot(Jakosc, jakosc_umiarkowana, label='umiarkowana')
ax2.plot(Jakosc, jakosc_dobra, label='dobra')
ax2.set_title('Wyjście: jakość')
ax2.set_xlabel('jakość')
ax2.set_ylabel('μ')
ax2.legend()
ax2.grid(True)

# WYKRES 3: charakterystyka FIS (jakość w funkcji PM)
pm_range = np.linspace(0, 150, 200)
wyjscia = [Wynik(p) for p in pm_range]
ax3.plot(pm_range, wyjscia, color='darkred')
ax3.set_title('Charakterystyka FIS (jakość w funkcji PM2.5)')
ax3.set_xlabel('PM2.5 [μg/m³]')
ax3.set_ylabel('Jakość')
ax3.grid(True)

plt.tight_layout()
plt.show()

# Wyświetlamy pierwsze 5 wierszy tabeli z 3 polami.
tabela = df[['PM2.5 [μg/m³]', 'Kategoria lingwistyczna', 'Wynik FIS (do uzupełnienia)']]
print(tabela.head(5))

# Zapis wyniku do baza.xlsx
# with pd.ExcelWriter(path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
#   df.to_excel(writer, sheet_name='A3_Jakość_powietrza', startrow=2, startcol=0, header=False, index=False)

# Interpretacja wyników dla pierwszych 5 wierszy:
# System rozmyty polegający na ocenie jakości powietrza, patrząc na pierwsze 5 wierszy 1,2 i 3 indeks charakteryzuje się wysokim współczynnikiem
# FIS >50 oraz kategorią lingwistyczną (niskie), wartość współczynnika FIS świadczy o tym, że pomimo danej wartości pyłu jakość powietrza jest dobra.
# Indeks 2 o kategorii (umiarkowane) oraz PM2.5 = 59.8 cechuje współczynnik FIS na poziomie <50, natomiast indeks o PM2.5 = 75.9 oraz kategorii (wysokie)
# to wartość FIS około 22, czyli o wiele niższa niż poprzednie. Im niższa wartość FIS tym jakość powietrza jest gorsza, im wyższa tym jakość powietrza jest lepsza.