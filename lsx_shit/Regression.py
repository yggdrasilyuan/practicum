import json
import os
import math
import numpy as np
import pandas as pd
from scipy.special import comb
import scipy.stats

json_file = open("sp500_bb.json", 'r', encoding='utf-8')
desktop_path = os.path.expanduser("~/Desktop")
json_file_path = os.path.join(desktop_path, "sp500_bb.json")
# period_data = json.load("/Users/shuxianglei/Desktop/sp500_bb.json")
with open(json_file_path, "r") as f:
    period_data = json.load(f)
Bull = period_data['bull']
Bear = period_data['bear']

print('Mean of Bull: ', np.mean(Bull), 'Mean of Bear: ', np.mean(Bear))
print("Stationary Prob of Bull:", round(np.mean(Bull) / (np.mean(Bull) + np.mean(Bear)) * 100, 2),
      "Stationary Prob of Bear:", round(np.mean(Bear) / (np.mean(Bull) + np.mean(Bear)) * 100, 2))

dict = {}

for q in range(1, 7):  # NB(1)  NB(2)  NB(3)  NB(4)  NB(5)  NB(6)
    p_bull = len(Bull) * q / (len(Bull) * q + sum(Bull))  # transition probability between two sub-states
    p_bear = len(Bear) * q / (len(Bear) * q + sum(Bear))  # transition probability between two sub-states
    L_bull_l = [np.log(max(1, comb(int(Bull[i]) - 1, int(Bull[i]) - q))) + q * np.log(p_bull) + (Bull[i] - q) * np.log(
        1 - p_bull) for i in range(len(Bull))]
    L_bull = np.sum(L_bull_l)
    L_bear_l = [np.log(max(1, comb(int(Bear[i]), q - 1))) + q * np.log(p_bear) + (Bull[i] - q) * np.log(1 - p_bear) for
                i in range(len(Bear))]
    L_bear = np.sum(L_bear_l)
    print(q, round(p_bull, 2), round(L_bull, 2), round(p_bear, 2), round(L_bear, 2))
    P = np.zeros((2 * q, 2 * q))
    for i in range(q):
        P[i, i] = 1 - p_bull
        P[i, i + 1] = p_bull
        P[i + q, i + q] = 1 - p_bear
        if i + q + 1 < q * 2:
            P[i + q, i + q + 1] = p_bear
        else:
            P[i + q, 0] = p_bear
    # print(P)

    Pk_list = [P]
    Pk = P
    PAAk = [np.sum(Pk[:q,:q])/q]
    PBBk = [np.sum(Pk[q:,q:])/q]
    for k in range(300):
        Pk = Pk @ P
        if k < 29:
            Pk_list.append(Pk)
            PAAk.append(np.sum(Pk[:q,:q])/q)
            PBBk.append(np.sum(Pk[q:,q:])/q)
        elif k == 299:
            # print(Pk)
            pi_bull = Pk[0, 0] / (Pk[0, 0] + Pk[0, q])
            pi_bear = Pk[0, q] / (Pk[0, 0] + Pk[0, q])
# print(len(PAAk))
# print(len(PBBk))
    miua = 0.08278787878787879
    miub = -0.08621875
    miu = pi_bull*0.08278787878787879 + pi_bear*(-0.08621875)
    var = pi_bull * 0.007626591368227733 + pi_bear * 0.011494295898437498 + pi_bear*pi_bull*((miua - miub)**2)

    expection = []
    for i in range(0, len(PAAk)):
        expection.append(pi_bull*miua*(PAAk[i]*miua + (1 - PAAk[i])*miub) + pi_bear*miub*(((1-PBBk[i])*miua) + PBBk[i]*miub))
    # print(expection)

    rhok = []
    for i in range(0, len(expection)):
        rhok.append((expection[i] - miu**2) / var)
    # print(rhok)

    Rpp = np.zeros((30,30))
    for i in range(30):
        for j in range(30):
            Rpp[i,j] = rhok[abs(i-j)-1] if i!=j else 1
    # print(Rpp)

    # Then compute AR coefficient Phi_p, make the sum equal to 1
    Phi_p = np.linalg.inv(Rpp)@np.array(rhok)
    theta = Phi_p / np.sum(Phi_p)
    # print(theta)

    Rnp = np.zeros((30,30))
    for i in range(30):
        for j in range(30):
            Rnp[i,j] = rhok[abs(i-j)-1] if i!=j else 1

    theta1 = theta.T

    ONE = np.ones((30,1))

    m = theta1@ONE*miu

    Rnn = Rpp.copy()

    v = np.sqrt(theta1@Rnn@theta*var)

    d = -(m/v)

    fd = []

    for i in range(0, len(d)):
        fd.append(1 / np.sqrt(2 * np.pi) * np.exp(-(d**2) / 2))

    koppa = (theta1@Rnp@Phi_p) / np.sqrt(theta1@Rnn@theta)

    phi_d = scipy.stats.norm.cdf(d)
    phi_d1 = scipy.stats.norm.cdf(-d)

    fd1 = fd[0]

    g = np.sqrt(var) * koppa * fd1

    rf = 0.015

    Ert = (miu - rf)*phi_d1 + rf + g

    Varrt = (miu**2 + var) * phi_d + g*(2*miu + np.sqrt(var)*koppa*d) + (rf**2) * phi_d - (Ert**2)

    alphart = g * (1 - (((miu - rf) * (miu - rf + np.sqrt(var)*koppa*d)) / var))

    SRrt = ((Ert - rf)) / (np.sqrt(Varrt))

    # print(SRrt, alphart)
    # theta111 = dict ['{}'.format(q):theta.tolist()]
    # json_str = json.dumps(theta111)
    # with open("theta111","w",encoding="utf-8") as json_file:
    #     json_file.write(json_str)
    #     json_file.close()

