pragma circom 2.0.0;

template SBoxAlpha() {
    signal input in;
    signal output out;
    signal t1;
    t1 <== in * in;
    signal t2;
    t2 <== t1 * in;
    out <== t2;
}

template Poseidon1T3_poseidon2_sparse() {
    signal input in[3];
    signal output out[3];
    signal state[33][3];
    for (var i = 0; i < 3; i++) { state[0][i] <== in[i]; }
    component sbox[32][3];

    // round 0 [full]
    sbox[0][0] = SBoxAlpha();
    sbox[0][0].in <== state[0][0] + 174080982;
    sbox[0][1] = SBoxAlpha();
    sbox[0][1].in <== state[0][1] + 1893211032;
    sbox[0][2] = SBoxAlpha();
    sbox[0][2].in <== state[0][2] + 205796291;
    state[1][0] <== 630515943 * sbox[0][0].out + 124443138 * sbox[0][1].out + 1067104518 * sbox[0][2].out;
    state[1][1] <== 914440123 * sbox[0][0].out + 229794830 * sbox[0][1].out + 704986396 * sbox[0][2].out;
    state[1][2] <== 558845607 * sbox[0][0].out + 1055005211 * sbox[0][1].out + 1277817208 * sbox[0][2].out;

    // round 1 [full]
    sbox[1][0] = SBoxAlpha();
    sbox[1][0].in <== state[1][0] + 654312535;
    sbox[1][1] = SBoxAlpha();
    sbox[1][1].in <== state[1][1] + 1558673435;
    sbox[1][2] = SBoxAlpha();
    sbox[1][2].in <== state[1][2] + 834558197;
    state[2][0] <== 630515943 * sbox[1][0].out + 124443138 * sbox[1][1].out + 1067104518 * sbox[1][2].out;
    state[2][1] <== 914440123 * sbox[1][0].out + 229794830 * sbox[1][1].out + 704986396 * sbox[1][2].out;
    state[2][2] <== 558845607 * sbox[1][0].out + 1055005211 * sbox[1][1].out + 1277817208 * sbox[1][2].out;

    // round 2 [full]
    sbox[2][0] = SBoxAlpha();
    sbox[2][0].in <== state[2][0] + 699013172;
    sbox[2][1] = SBoxAlpha();
    sbox[2][1].in <== state[2][1] + 1874537604;
    sbox[2][2] = SBoxAlpha();
    sbox[2][2].in <== state[2][2] + 1084610695;
    state[3][0] <== 630515943 * sbox[2][0].out + 124443138 * sbox[2][1].out + 1067104518 * sbox[2][2].out;
    state[3][1] <== 914440123 * sbox[2][0].out + 229794830 * sbox[2][1].out + 704986396 * sbox[2][2].out;
    state[3][2] <== 558845607 * sbox[2][0].out + 1055005211 * sbox[2][1].out + 1277817208 * sbox[2][2].out;

    // round 3 [full]
    sbox[3][0] = SBoxAlpha();
    sbox[3][0].in <== state[3][0] + 1077809999;
    sbox[3][1] = SBoxAlpha();
    sbox[3][1].in <== state[3][1] + 1016014712;
    sbox[3][2] = SBoxAlpha();
    sbox[3][2].in <== state[3][2] + 838216989;
    state[4][0] <== 630515943 * sbox[3][0].out + 124443138 * sbox[3][1].out + 1067104518 * sbox[3][2].out;
    state[4][1] <== 914440123 * sbox[3][0].out + 229794830 * sbox[3][1].out + 704986396 * sbox[3][2].out;
    state[4][2] <== 558845607 * sbox[3][0].out + 1055005211 * sbox[3][1].out + 1277817208 * sbox[3][2].out;

    // round 4 [full]
    sbox[4][0] = SBoxAlpha();
    sbox[4][0].in <== state[4][0] + 489058490;
    sbox[4][1] = SBoxAlpha();
    sbox[4][1].in <== state[4][1] + 1298540828;
    sbox[4][2] = SBoxAlpha();
    sbox[4][2].in <== state[4][2] + 675269264;
    state[5][0] <== 630515943 * sbox[4][0].out + 124443138 * sbox[4][1].out + 1067104518 * sbox[4][2].out;
    state[5][1] <== 914440123 * sbox[4][0].out + 229794830 * sbox[4][1].out + 704986396 * sbox[4][2].out;
    state[5][2] <== 558845607 * sbox[4][0].out + 1055005211 * sbox[4][1].out + 1277817208 * sbox[4][2].out;

    // round 5 [full]
    sbox[5][0] = SBoxAlpha();
    sbox[5][0].in <== state[5][0] + 1144188477;
    sbox[5][1] = SBoxAlpha();
    sbox[5][1].in <== state[5][1] + 1091277470;
    sbox[5][2] = SBoxAlpha();
    sbox[5][2].in <== state[5][2] + 181587216;
    state[6][0] <== 630515943 * sbox[5][0].out + 124443138 * sbox[5][1].out + 1067104518 * sbox[5][2].out;
    state[6][1] <== 914440123 * sbox[5][0].out + 229794830 * sbox[5][1].out + 704986396 * sbox[5][2].out;
    state[6][2] <== 558845607 * sbox[5][0].out + 1055005211 * sbox[5][1].out + 1277817208 * sbox[5][2].out;

    // round 6 [partial]
    sbox[6][0] = SBoxAlpha();
    sbox[6][0].in <== state[6][0] + 1643877511;
    state[7][0] <== 1568040038 * sbox[6][0].out + 1 * (state[6][1] + 1158567799) + 1 * (state[6][2] + 1938780621);
    state[7][1] <== 1 * sbox[6][0].out + 1676976621 * (state[6][1] + 1158567799) + 1 * (state[6][2] + 1938780621);
    state[7][2] <== 1 * sbox[6][0].out + 1 * (state[6][1] + 1158567799) + 1818300880 * (state[6][2] + 1938780621);

    // round 7 [partial]
    sbox[7][0] = SBoxAlpha();
    sbox[7][0].in <== state[7][0] + 830993030;
    state[8][0] <== 1568040038 * sbox[7][0].out + 1 * (state[7][1] + 1330997606) + 1 * (state[7][2] + 1193630922);
    state[8][1] <== 1 * sbox[7][0].out + 1676976621 * (state[7][1] + 1330997606) + 1 * (state[7][2] + 1193630922);
    state[8][2] <== 1 * sbox[7][0].out + 1 * (state[7][1] + 1330997606) + 1818300880 * (state[7][2] + 1193630922);

    // round 8 [partial]
    sbox[8][0] = SBoxAlpha();
    sbox[8][0].in <== state[8][0] + 1894971516;
    state[9][0] <== 1568040038 * sbox[8][0].out + 1 * (state[8][1] + 1269526856) + 1 * (state[8][2] + 1531944748);
    state[9][1] <== 1 * sbox[8][0].out + 1676976621 * (state[8][1] + 1269526856) + 1 * (state[8][2] + 1531944748);
    state[9][2] <== 1 * sbox[8][0].out + 1 * (state[8][1] + 1269526856) + 1818300880 * (state[8][2] + 1531944748);

    // round 9 [partial]
    sbox[9][0] = SBoxAlpha();
    sbox[9][0].in <== state[9][0] + 1544783405;
    state[10][0] <== 1568040038 * sbox[9][0].out + 1 * (state[9][1] + 2009896675) + 1 * (state[9][2] + 2048826439);
    state[10][1] <== 1 * sbox[9][0].out + 1676976621 * (state[9][1] + 2009896675) + 1 * (state[9][2] + 2048826439);
    state[10][2] <== 1 * sbox[9][0].out + 1 * (state[9][1] + 2009896675) + 1818300880 * (state[9][2] + 2048826439);

    // round 10 [partial]
    sbox[10][0] = SBoxAlpha();
    sbox[10][0].in <== state[10][0] + 1792866707;
    state[11][0] <== 1568040038 * sbox[10][0].out + 1 * (state[10][1] + 731708398) + 1 * (state[10][2] + 1214853430);
    state[11][1] <== 1 * sbox[10][0].out + 1676976621 * (state[10][1] + 731708398) + 1 * (state[10][2] + 1214853430);
    state[11][2] <== 1 * sbox[10][0].out + 1 * (state[10][1] + 731708398) + 1818300880 * (state[10][2] + 1214853430);

    // round 11 [partial]
    sbox[11][0] = SBoxAlpha();
    sbox[11][0].in <== state[11][0] + 1772137973;
    state[12][0] <== 1568040038 * sbox[11][0].out + 1 * (state[11][1] + 1382070080) + 1 * (state[11][2] + 1693412733);
    state[12][1] <== 1 * sbox[11][0].out + 1676976621 * (state[11][1] + 1382070080) + 1 * (state[11][2] + 1693412733);
    state[12][2] <== 1 * sbox[11][0].out + 1 * (state[11][1] + 1382070080) + 1818300880 * (state[11][2] + 1693412733);

    // round 12 [partial]
    sbox[12][0] = SBoxAlpha();
    sbox[12][0].in <== state[12][0] + 1412378934;
    state[13][0] <== 1568040038 * sbox[12][0].out + 1 * (state[12][1] + 1904286071) + 1 * (state[12][2] + 676555353);
    state[13][1] <== 1 * sbox[12][0].out + 1676976621 * (state[12][1] + 1904286071) + 1 * (state[12][2] + 676555353);
    state[13][2] <== 1 * sbox[12][0].out + 1 * (state[12][1] + 1904286071) + 1818300880 * (state[12][2] + 676555353);

    // round 13 [partial]
    sbox[13][0] = SBoxAlpha();
    sbox[13][0].in <== state[13][0] + 250863045;
    state[14][0] <== 1568040038 * sbox[13][0].out + 1 * (state[13][1] + 708764137) + 1 * (state[13][2] + 1175013586);
    state[14][1] <== 1 * sbox[13][0].out + 1676976621 * (state[13][1] + 708764137) + 1 * (state[13][2] + 1175013586);
    state[14][2] <== 1 * sbox[13][0].out + 1 * (state[13][1] + 708764137) + 1818300880 * (state[13][2] + 1175013586);

    // round 14 [partial]
    sbox[14][0] = SBoxAlpha();
    sbox[14][0].in <== state[14][0] + 1151550354;
    state[15][0] <== 1568040038 * sbox[14][0].out + 1 * (state[14][1] + 40600458) + 1 * (state[14][2] + 764536358);
    state[15][1] <== 1 * sbox[14][0].out + 1676976621 * (state[14][1] + 40600458) + 1 * (state[14][2] + 764536358);
    state[15][2] <== 1 * sbox[14][0].out + 1 * (state[14][1] + 40600458) + 1818300880 * (state[14][2] + 764536358);

    // round 15 [partial]
    sbox[15][0] = SBoxAlpha();
    sbox[15][0].in <== state[15][0] + 1950955894;
    state[16][0] <== 1568040038 * sbox[15][0].out + 1 * (state[15][1] + 382293863) + 1 * (state[15][2] + 426692504);
    state[16][1] <== 1 * sbox[15][0].out + 1676976621 * (state[15][1] + 382293863) + 1 * (state[15][2] + 426692504);
    state[16][2] <== 1 * sbox[15][0].out + 1 * (state[15][1] + 382293863) + 1818300880 * (state[15][2] + 426692504);

    // round 16 [partial]
    sbox[16][0] = SBoxAlpha();
    sbox[16][0].in <== state[16][0] + 4893290;
    state[17][0] <== 1568040038 * sbox[16][0].out + 1 * (state[16][1] + 710353494) + 1 * (state[16][2] + 461247272);
    state[17][1] <== 1 * sbox[16][0].out + 1676976621 * (state[16][1] + 710353494) + 1 * (state[16][2] + 461247272);
    state[17][2] <== 1 * sbox[16][0].out + 1 * (state[16][1] + 710353494) + 1818300880 * (state[16][2] + 461247272);

    // round 17 [partial]
    sbox[17][0] = SBoxAlpha();
    sbox[17][0].in <== state[17][0] + 638440502;
    state[18][0] <== 1568040038 * sbox[17][0].out + 1 * (state[17][1] + 538914736) + 1 * (state[17][2] + 2125502993);
    state[18][1] <== 1 * sbox[17][0].out + 1676976621 * (state[17][1] + 538914736) + 1 * (state[17][2] + 2125502993);
    state[18][2] <== 1 * sbox[17][0].out + 1 * (state[17][1] + 538914736) + 1818300880 * (state[17][2] + 2125502993);

    // round 18 [partial]
    sbox[18][0] = SBoxAlpha();
    sbox[18][0].in <== state[18][0] + 400512040;
    state[19][0] <== 1568040038 * sbox[18][0].out + 1 * (state[18][1] + 144218311) + 1 * (state[18][2] + 2115802290);
    state[19][1] <== 1 * sbox[18][0].out + 1676976621 * (state[18][1] + 144218311) + 1 * (state[18][2] + 2115802290);
    state[19][2] <== 1 * sbox[18][0].out + 1 * (state[18][1] + 144218311) + 1818300880 * (state[18][2] + 2115802290);

    // round 19 [partial]
    sbox[19][0] = SBoxAlpha();
    sbox[19][0].in <== state[19][0] + 1422327705;
    state[20][0] <== 1568040038 * sbox[19][0].out + 1 * (state[19][1] + 1169644204) + 1 * (state[19][2] + 953527017);
    state[20][1] <== 1 * sbox[19][0].out + 1676976621 * (state[19][1] + 1169644204) + 1 * (state[19][2] + 953527017);
    state[20][2] <== 1 * sbox[19][0].out + 1 * (state[19][1] + 1169644204) + 1818300880 * (state[19][2] + 953527017);

    // round 20 [partial]
    sbox[20][0] = SBoxAlpha();
    sbox[20][0].in <== state[20][0] + 1879494506;
    state[21][0] <== 1568040038 * sbox[20][0].out + 1 * (state[20][1] + 1089088251) + 1 * (state[20][2] + 496891716);
    state[21][1] <== 1 * sbox[20][0].out + 1676976621 * (state[20][1] + 1089088251) + 1 * (state[20][2] + 496891716);
    state[21][2] <== 1 * sbox[20][0].out + 1 * (state[20][1] + 1089088251) + 1818300880 * (state[20][2] + 496891716);

    // round 21 [partial]
    sbox[21][0] = SBoxAlpha();
    sbox[21][0].in <== state[21][0] + 1302073245;
    state[22][0] <== 1568040038 * sbox[21][0].out + 1 * (state[21][1] + 1205547847) + 1 * (state[21][2] + 18957766);
    state[22][1] <== 1 * sbox[21][0].out + 1676976621 * (state[21][1] + 1205547847) + 1 * (state[21][2] + 18957766);
    state[22][2] <== 1 * sbox[21][0].out + 1 * (state[21][1] + 1205547847) + 1818300880 * (state[21][2] + 18957766);

    // round 22 [partial]
    sbox[22][0] = SBoxAlpha();
    sbox[22][0].in <== state[22][0] + 1191475602;
    state[23][0] <== 1568040038 * sbox[22][0].out + 1 * (state[22][1] + 742884914) + 1 * (state[22][2] + 1506752765);
    state[23][1] <== 1 * sbox[22][0].out + 1676976621 * (state[22][1] + 742884914) + 1 * (state[22][2] + 1506752765);
    state[23][2] <== 1 * sbox[22][0].out + 1 * (state[22][1] + 742884914) + 1818300880 * (state[22][2] + 1506752765);

    // round 23 [partial]
    sbox[23][0] = SBoxAlpha();
    sbox[23][0].in <== state[23][0] + 1510763441;
    state[24][0] <== 1568040038 * sbox[23][0].out + 1 * (state[23][1] + 525699066) + 1 * (state[23][2] + 1464263037);
    state[24][1] <== 1 * sbox[23][0].out + 1676976621 * (state[23][1] + 525699066) + 1 * (state[23][2] + 1464263037);
    state[24][2] <== 1 * sbox[23][0].out + 1 * (state[23][1] + 525699066) + 1818300880 * (state[23][2] + 1464263037);

    // round 24 [partial]
    sbox[24][0] = SBoxAlpha();
    sbox[24][0].in <== state[24][0] + 315859625;
    state[25][0] <== 1568040038 * sbox[24][0].out + 1 * (state[24][1] + 1876104949) + 1 * (state[24][2] + 429578372);
    state[25][1] <== 1 * sbox[24][0].out + 1676976621 * (state[24][1] + 1876104949) + 1 * (state[24][2] + 429578372);
    state[25][2] <== 1 * sbox[24][0].out + 1 * (state[24][1] + 1876104949) + 1818300880 * (state[24][2] + 429578372);

    // round 25 [partial]
    sbox[25][0] = SBoxAlpha();
    sbox[25][0].in <== state[25][0] + 1897236304;
    state[26][0] <== 1568040038 * sbox[25][0].out + 1 * (state[25][1] + 45183642) + 1 * (state[25][2] + 178231105);
    state[26][1] <== 1 * sbox[25][0].out + 1676976621 * (state[25][1] + 45183642) + 1 * (state[25][2] + 178231105);
    state[26][2] <== 1 * sbox[25][0].out + 1 * (state[25][1] + 45183642) + 1818300880 * (state[25][2] + 178231105);

    // round 26 [full]
    sbox[26][0] = SBoxAlpha();
    sbox[26][0].in <== state[26][0] + 1647368937;
    sbox[26][1] = SBoxAlpha();
    sbox[26][1].in <== state[26][1] + 1917494054;
    sbox[26][2] = SBoxAlpha();
    sbox[26][2].in <== state[26][2] + 1726422498;
    state[27][0] <== 630515943 * sbox[26][0].out + 124443138 * sbox[26][1].out + 1067104518 * sbox[26][2].out;
    state[27][1] <== 914440123 * sbox[26][0].out + 229794830 * sbox[26][1].out + 704986396 * sbox[26][2].out;
    state[27][2] <== 558845607 * sbox[26][0].out + 1055005211 * sbox[26][1].out + 1277817208 * sbox[26][2].out;

    // round 27 [full]
    sbox[27][0] = SBoxAlpha();
    sbox[27][0].in <== state[27][0] + 2089001415;
    sbox[27][1] = SBoxAlpha();
    sbox[27][1].in <== state[27][1] + 1879935623;
    sbox[27][2] = SBoxAlpha();
    sbox[27][2].in <== state[27][2] + 745259239;
    state[28][0] <== 630515943 * sbox[27][0].out + 124443138 * sbox[27][1].out + 1067104518 * sbox[27][2].out;
    state[28][1] <== 914440123 * sbox[27][0].out + 229794830 * sbox[27][1].out + 704986396 * sbox[27][2].out;
    state[28][2] <== 558845607 * sbox[27][0].out + 1055005211 * sbox[27][1].out + 1277817208 * sbox[27][2].out;

    // round 28 [full]
    sbox[28][0] = SBoxAlpha();
    sbox[28][0].in <== state[28][0] + 279291263;
    sbox[28][1] = SBoxAlpha();
    sbox[28][1].in <== state[28][1] + 1419299990;
    sbox[28][2] = SBoxAlpha();
    sbox[28][2].in <== state[28][2] + 1179591362;
    state[29][0] <== 630515943 * sbox[28][0].out + 124443138 * sbox[28][1].out + 1067104518 * sbox[28][2].out;
    state[29][1] <== 914440123 * sbox[28][0].out + 229794830 * sbox[28][1].out + 704986396 * sbox[28][2].out;
    state[29][2] <== 558845607 * sbox[28][0].out + 1055005211 * sbox[28][1].out + 1277817208 * sbox[28][2].out;

    // round 29 [full]
    sbox[29][0] = SBoxAlpha();
    sbox[29][0].in <== state[29][0] + 858215978;
    sbox[29][1] = SBoxAlpha();
    sbox[29][1].in <== state[29][1] + 1125067920;
    sbox[29][2] = SBoxAlpha();
    sbox[29][2].in <== state[29][2] + 2002724547;
    state[30][0] <== 630515943 * sbox[29][0].out + 124443138 * sbox[29][1].out + 1067104518 * sbox[29][2].out;
    state[30][1] <== 914440123 * sbox[29][0].out + 229794830 * sbox[29][1].out + 704986396 * sbox[29][2].out;
    state[30][2] <== 558845607 * sbox[29][0].out + 1055005211 * sbox[29][1].out + 1277817208 * sbox[29][2].out;

    // round 30 [full]
    sbox[30][0] = SBoxAlpha();
    sbox[30][0].in <== state[30][0] + 1090299748;
    sbox[30][1] = SBoxAlpha();
    sbox[30][1].in <== state[30][1] + 459247318;
    sbox[30][2] = SBoxAlpha();
    sbox[30][2].in <== state[30][2] + 1859509203;
    state[31][0] <== 630515943 * sbox[30][0].out + 124443138 * sbox[30][1].out + 1067104518 * sbox[30][2].out;
    state[31][1] <== 914440123 * sbox[30][0].out + 229794830 * sbox[30][1].out + 704986396 * sbox[30][2].out;
    state[31][2] <== 558845607 * sbox[30][0].out + 1055005211 * sbox[30][1].out + 1277817208 * sbox[30][2].out;

    // round 31 [full]
    sbox[31][0] = SBoxAlpha();
    sbox[31][0].in <== state[31][0] + 575825686;
    sbox[31][1] = SBoxAlpha();
    sbox[31][1].in <== state[31][1] + 1708496481;
    sbox[31][2] = SBoxAlpha();
    sbox[31][2].in <== state[31][2] + 1923642035;
    state[32][0] <== 630515943 * sbox[31][0].out + 124443138 * sbox[31][1].out + 1067104518 * sbox[31][2].out;
    state[32][1] <== 914440123 * sbox[31][0].out + 229794830 * sbox[31][1].out + 704986396 * sbox[31][2].out;
    state[32][2] <== 558845607 * sbox[31][0].out + 1055005211 * sbox[31][1].out + 1277817208 * sbox[31][2].out;

    for (var i = 0; i < 3; i++) { out[i] <== state[32][i]; }
}

component main = Poseidon1T3_poseidon2_sparse();