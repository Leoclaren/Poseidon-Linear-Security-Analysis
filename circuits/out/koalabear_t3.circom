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
    signal state[29][3];
    for (var i = 0; i < 3; i++) { state[0][i] <== in[i]; }
    component sbox[28][3];

    // round 0 [full]
    sbox[0][0] = SBoxAlpha();
    sbox[0][0].in <== state[0][0] + 1306538447;
    sbox[0][1] = SBoxAlpha();
    sbox[0][1].in <== state[0][1] + 285352558;
    sbox[0][2] = SBoxAlpha();
    sbox[0][2].in <== state[0][2] + 1505762002;
    state[1][0] <== 630515943 * sbox[0][0].out + 124443138 * sbox[0][1].out + 1067104518 * sbox[0][2].out;
    state[1][1] <== 914440123 * sbox[0][0].out + 229794830 * sbox[0][1].out + 704986396 * sbox[0][2].out;
    state[1][2] <== 558845607 * sbox[0][0].out + 1055005211 * sbox[0][1].out + 1277817208 * sbox[0][2].out;

    // round 1 [full]
    sbox[1][0] = SBoxAlpha();
    sbox[1][0].in <== state[1][0] + 433453630;
    sbox[1][1] = SBoxAlpha();
    sbox[1][1].in <== state[1][1] + 635692046;
    sbox[1][2] = SBoxAlpha();
    sbox[1][2].in <== state[1][2] + 1679502601;
    state[2][0] <== 630515943 * sbox[1][0].out + 124443138 * sbox[1][1].out + 1067104518 * sbox[1][2].out;
    state[2][1] <== 914440123 * sbox[1][0].out + 229794830 * sbox[1][1].out + 704986396 * sbox[1][2].out;
    state[2][2] <== 558845607 * sbox[1][0].out + 1055005211 * sbox[1][1].out + 1277817208 * sbox[1][2].out;

    // round 2 [full]
    sbox[2][0] = SBoxAlpha();
    sbox[2][0].in <== state[2][0] + 1972283851;
    sbox[2][1] = SBoxAlpha();
    sbox[2][1].in <== state[2][1] + 898857955;
    sbox[2][2] = SBoxAlpha();
    sbox[2][2].in <== state[2][2] + 1669746823;
    state[3][0] <== 630515943 * sbox[2][0].out + 124443138 * sbox[2][1].out + 1067104518 * sbox[2][2].out;
    state[3][1] <== 914440123 * sbox[2][0].out + 229794830 * sbox[2][1].out + 704986396 * sbox[2][2].out;
    state[3][2] <== 558845607 * sbox[2][0].out + 1055005211 * sbox[2][1].out + 1277817208 * sbox[2][2].out;

    // round 3 [full]
    sbox[3][0] = SBoxAlpha();
    sbox[3][0].in <== state[3][0] + 252943947;
    sbox[3][1] = SBoxAlpha();
    sbox[3][1].in <== state[3][1] + 1811926692;
    sbox[3][2] = SBoxAlpha();
    sbox[3][2].in <== state[3][2] + 753327105;
    state[4][0] <== 630515943 * sbox[3][0].out + 124443138 * sbox[3][1].out + 1067104518 * sbox[3][2].out;
    state[4][1] <== 914440123 * sbox[3][0].out + 229794830 * sbox[3][1].out + 704986396 * sbox[3][2].out;
    state[4][2] <== 558845607 * sbox[3][0].out + 1055005211 * sbox[3][1].out + 1277817208 * sbox[3][2].out;

    // round 4 [partial]
    sbox[4][0] = SBoxAlpha();
    sbox[4][0].in <== state[4][0] + 1639080270;
    state[5][0] <== 1568040038 * sbox[4][0].out + 1 * (state[4][1] + 2063035259) + 1 * (state[4][2] + 466256845);
    state[5][1] <== 1 * sbox[4][0].out + 1676976621 * (state[4][1] + 2063035259) + 1 * (state[4][2] + 466256845);
    state[5][2] <== 1 * sbox[4][0].out + 1 * (state[4][1] + 2063035259) + 1818300880 * (state[4][2] + 466256845);

    // round 5 [partial]
    sbox[5][0] = SBoxAlpha();
    sbox[5][0].in <== state[5][0] + 1451236244;
    state[6][0] <== 1568040038 * sbox[5][0].out + 1 * (state[5][1] + 1828447996) + 1 * (state[5][2] + 580098228);
    state[6][1] <== 1 * sbox[5][0].out + 1676976621 * (state[5][1] + 1828447996) + 1 * (state[5][2] + 580098228);
    state[6][2] <== 1 * sbox[5][0].out + 1 * (state[5][1] + 1828447996) + 1818300880 * (state[5][2] + 580098228);

    // round 6 [partial]
    sbox[6][0] = SBoxAlpha();
    sbox[6][0].in <== state[6][0] + 517678997;
    state[7][0] <== 1568040038 * sbox[6][0].out + 1 * (state[6][1] + 2042883155) + 1 * (state[6][2] + 322344086);
    state[7][1] <== 1 * sbox[6][0].out + 1676976621 * (state[6][1] + 2042883155) + 1 * (state[6][2] + 322344086);
    state[7][2] <== 1 * sbox[6][0].out + 1 * (state[6][1] + 2042883155) + 1818300880 * (state[6][2] + 322344086);

    // round 7 [partial]
    sbox[7][0] = SBoxAlpha();
    sbox[7][0].in <== state[7][0] + 1348040016;
    state[8][0] <== 1568040038 * sbox[7][0].out + 1 * (state[7][1] + 1646137735) + 1 * (state[7][2] + 117652143);
    state[8][1] <== 1 * sbox[7][0].out + 1676976621 * (state[7][1] + 1646137735) + 1 * (state[7][2] + 117652143);
    state[8][2] <== 1 * sbox[7][0].out + 1 * (state[7][1] + 1646137735) + 1818300880 * (state[7][2] + 117652143);

    // round 8 [partial]
    sbox[8][0] = SBoxAlpha();
    sbox[8][0].in <== state[8][0] + 2063036632;
    state[9][0] <== 1568040038 * sbox[8][0].out + 1 * (state[8][1] + 1166694321) + 1 * (state[8][2] + 393503720);
    state[9][1] <== 1 * sbox[8][0].out + 1676976621 * (state[8][1] + 1166694321) + 1 * (state[8][2] + 393503720);
    state[9][2] <== 1 * sbox[8][0].out + 1 * (state[8][1] + 1166694321) + 1818300880 * (state[8][2] + 393503720);

    // round 9 [partial]
    sbox[9][0] = SBoxAlpha();
    sbox[9][0].in <== state[9][0] + 1835527871;
    state[10][0] <== 1568040038 * sbox[9][0].out + 1 * (state[9][1] + 1439230016) + 1 * (state[9][2] + 809351049);
    state[10][1] <== 1 * sbox[9][0].out + 1676976621 * (state[9][1] + 1439230016) + 1 * (state[9][2] + 809351049);
    state[10][2] <== 1 * sbox[9][0].out + 1 * (state[9][1] + 1439230016) + 1818300880 * (state[9][2] + 809351049);

    // round 10 [partial]
    sbox[10][0] = SBoxAlpha();
    sbox[10][0].in <== state[10][0] + 1660134552;
    state[11][0] <== 1568040038 * sbox[10][0].out + 1 * (state[10][1] + 2093867489) + 1 * (state[10][2] + 653361465);
    state[11][1] <== 1 * sbox[10][0].out + 1676976621 * (state[10][1] + 2093867489) + 1 * (state[10][2] + 653361465);
    state[11][2] <== 1 * sbox[10][0].out + 1 * (state[10][1] + 2093867489) + 1818300880 * (state[10][2] + 653361465);

    // round 11 [partial]
    sbox[11][0] = SBoxAlpha();
    sbox[11][0].in <== state[11][0] + 1120063209;
    state[12][0] <== 1568040038 * sbox[11][0].out + 1 * (state[11][1] + 660420446) + 1 * (state[11][2] + 241460862);
    state[12][1] <== 1 * sbox[11][0].out + 1676976621 * (state[11][1] + 660420446) + 1 * (state[11][2] + 241460862);
    state[12][2] <== 1 * sbox[11][0].out + 1 * (state[11][1] + 660420446) + 1818300880 * (state[11][2] + 241460862);

    // round 12 [partial]
    sbox[12][0] = SBoxAlpha();
    sbox[12][0].in <== state[12][0] + 2037957459;
    state[13][0] <== 1568040038 * sbox[12][0].out + 1 * (state[12][1] + 253722700) + 1 * (state[12][2] + 930944596);
    state[13][1] <== 1 * sbox[12][0].out + 1676976621 * (state[12][1] + 253722700) + 1 * (state[12][2] + 930944596);
    state[13][2] <== 1 * sbox[12][0].out + 1 * (state[12][1] + 253722700) + 1818300880 * (state[12][2] + 930944596);

    // round 13 [partial]
    sbox[13][0] = SBoxAlpha();
    sbox[13][0].in <== state[13][0] + 311787166;
    state[14][0] <== 1568040038 * sbox[13][0].out + 1 * (state[13][1] + 1150766933) + 1 * (state[13][2] + 565695909);
    state[14][1] <== 1 * sbox[13][0].out + 1676976621 * (state[13][1] + 1150766933) + 1 * (state[13][2] + 565695909);
    state[14][2] <== 1 * sbox[13][0].out + 1 * (state[13][1] + 1150766933) + 1818300880 * (state[13][2] + 565695909);

    // round 14 [partial]
    sbox[14][0] = SBoxAlpha();
    sbox[14][0].in <== state[14][0] + 1541360650;
    state[15][0] <== 1568040038 * sbox[14][0].out + 1 * (state[14][1] + 776085956) + 1 * (state[14][2] + 1621191806);
    state[15][1] <== 1 * sbox[14][0].out + 1676976621 * (state[14][1] + 776085956) + 1 * (state[14][2] + 1621191806);
    state[15][2] <== 1 * sbox[14][0].out + 1 * (state[14][1] + 776085956) + 1818300880 * (state[14][2] + 1621191806);

    // round 15 [partial]
    sbox[15][0] = SBoxAlpha();
    sbox[15][0].in <== state[15][0] + 1217491493;
    state[16][0] <== 1568040038 * sbox[15][0].out + 1 * (state[15][1] + 241886843) + 1 * (state[15][2] + 1679593081);
    state[16][1] <== 1 * sbox[15][0].out + 1676976621 * (state[15][1] + 241886843) + 1 * (state[15][2] + 1679593081);
    state[16][2] <== 1 * sbox[15][0].out + 1 * (state[15][1] + 241886843) + 1818300880 * (state[15][2] + 1679593081);

    // round 16 [partial]
    sbox[16][0] = SBoxAlpha();
    sbox[16][0].in <== state[16][0] + 393202786;
    state[17][0] <== 1568040038 * sbox[16][0].out + 1 * (state[16][1] + 1543810863) + 1 * (state[16][2] + 352183131);
    state[17][1] <== 1 * sbox[16][0].out + 1676976621 * (state[16][1] + 1543810863) + 1 * (state[16][2] + 352183131);
    state[17][2] <== 1 * sbox[16][0].out + 1 * (state[16][1] + 1543810863) + 1818300880 * (state[16][2] + 352183131);

    // round 17 [partial]
    sbox[17][0] = SBoxAlpha();
    sbox[17][0].in <== state[17][0] + 1953950250;
    state[18][0] <== 1568040038 * sbox[17][0].out + 1 * (state[17][1] + 1061244633) + 1 * (state[17][2] + 755199507);
    state[18][1] <== 1 * sbox[17][0].out + 1676976621 * (state[17][1] + 1061244633) + 1 * (state[17][2] + 755199507);
    state[18][2] <== 1 * sbox[17][0].out + 1 * (state[17][1] + 1061244633) + 1818300880 * (state[17][2] + 755199507);

    // round 18 [partial]
    sbox[18][0] = SBoxAlpha();
    sbox[18][0].in <== state[18][0] + 790730322;
    state[19][0] <== 1568040038 * sbox[18][0].out + 1 * (state[18][1] + 1274305225) + 1 * (state[18][2] + 1187194583);
    state[19][1] <== 1 * sbox[18][0].out + 1676976621 * (state[18][1] + 1274305225) + 1 * (state[18][2] + 1187194583);
    state[19][2] <== 1 * sbox[18][0].out + 1 * (state[18][1] + 1274305225) + 1818300880 * (state[18][2] + 1187194583);

    // round 19 [partial]
    sbox[19][0] = SBoxAlpha();
    sbox[19][0].in <== state[19][0] + 1168835628;
    state[20][0] <== 1568040038 * sbox[19][0].out + 1 * (state[19][1] + 325597108) + 1 * (state[19][2] + 865401144);
    state[20][1] <== 1 * sbox[19][0].out + 1676976621 * (state[19][1] + 325597108) + 1 * (state[19][2] + 865401144);
    state[20][2] <== 1 * sbox[19][0].out + 1 * (state[19][1] + 325597108) + 1818300880 * (state[19][2] + 865401144);

    // round 20 [partial]
    sbox[20][0] = SBoxAlpha();
    sbox[20][0].in <== state[20][0] + 1596164334;
    state[21][0] <== 1568040038 * sbox[20][0].out + 1 * (state[20][1] + 525668317) + 1 * (state[20][2] + 108467509);
    state[21][1] <== 1 * sbox[20][0].out + 1676976621 * (state[20][1] + 525668317) + 1 * (state[20][2] + 108467509);
    state[21][2] <== 1 * sbox[20][0].out + 1 * (state[20][1] + 525668317) + 1818300880 * (state[20][2] + 108467509);

    // round 21 [partial]
    sbox[21][0] = SBoxAlpha();
    sbox[21][0].in <== state[21][0] + 296431337;
    state[22][0] <== 1568040038 * sbox[21][0].out + 1 * (state[21][1] + 815641680) + 1 * (state[21][2] + 359199448);
    state[22][1] <== 1 * sbox[21][0].out + 1676976621 * (state[21][1] + 815641680) + 1 * (state[21][2] + 359199448);
    state[22][2] <== 1 * sbox[21][0].out + 1 * (state[21][1] + 815641680) + 1818300880 * (state[21][2] + 359199448);

    // round 22 [partial]
    sbox[22][0] = SBoxAlpha();
    sbox[22][0].in <== state[22][0] + 1463683788;
    state[23][0] <== 1568040038 * sbox[22][0].out + 1 * (state[22][1] + 1180385028) + 1 * (state[22][2] + 2094700075);
    state[23][1] <== 1 * sbox[22][0].out + 1676976621 * (state[22][1] + 1180385028) + 1 * (state[22][2] + 2094700075);
    state[23][2] <== 1 * sbox[22][0].out + 1 * (state[22][1] + 1180385028) + 1818300880 * (state[22][2] + 2094700075);

    // round 23 [partial]
    sbox[23][0] = SBoxAlpha();
    sbox[23][0].in <== state[23][0] + 1750893408;
    state[24][0] <== 1568040038 * sbox[23][0].out + 1 * (state[23][1] + 1108265739) + 1 * (state[23][2] + 990781987);
    state[24][1] <== 1 * sbox[23][0].out + 1676976621 * (state[23][1] + 1108265739) + 1 * (state[23][2] + 990781987);
    state[24][2] <== 1 * sbox[23][0].out + 1 * (state[23][1] + 1108265739) + 1818300880 * (state[23][2] + 990781987);

    // round 24 [full]
    sbox[24][0] = SBoxAlpha();
    sbox[24][0].in <== state[24][0] + 681424738;
    sbox[24][1] = SBoxAlpha();
    sbox[24][1].in <== state[24][1] + 436138636;
    sbox[24][2] = SBoxAlpha();
    sbox[24][2].in <== state[24][2] + 1744064163;
    state[25][0] <== 630515943 * sbox[24][0].out + 124443138 * sbox[24][1].out + 1067104518 * sbox[24][2].out;
    state[25][1] <== 914440123 * sbox[24][0].out + 229794830 * sbox[24][1].out + 704986396 * sbox[24][2].out;
    state[25][2] <== 558845607 * sbox[24][0].out + 1055005211 * sbox[24][1].out + 1277817208 * sbox[24][2].out;

    // round 25 [full]
    sbox[25][0] = SBoxAlpha();
    sbox[25][0].in <== state[25][0] + 908255193;
    sbox[25][1] = SBoxAlpha();
    sbox[25][1].in <== state[25][1] + 1735326064;
    sbox[25][2] = SBoxAlpha();
    sbox[25][2].in <== state[25][2] + 335568958;
    state[26][0] <== 630515943 * sbox[25][0].out + 124443138 * sbox[25][1].out + 1067104518 * sbox[25][2].out;
    state[26][1] <== 914440123 * sbox[25][0].out + 229794830 * sbox[25][1].out + 704986396 * sbox[25][2].out;
    state[26][2] <== 558845607 * sbox[25][0].out + 1055005211 * sbox[25][1].out + 1277817208 * sbox[25][2].out;

    // round 26 [full]
    sbox[26][0] = SBoxAlpha();
    sbox[26][0].in <== state[26][0] + 643325557;
    sbox[26][1] = SBoxAlpha();
    sbox[26][1].in <== state[26][1] + 1826280561;
    sbox[26][2] = SBoxAlpha();
    sbox[26][2].in <== state[26][2] + 319039156;
    state[27][0] <== 630515943 * sbox[26][0].out + 124443138 * sbox[26][1].out + 1067104518 * sbox[26][2].out;
    state[27][1] <== 914440123 * sbox[26][0].out + 229794830 * sbox[26][1].out + 704986396 * sbox[26][2].out;
    state[27][2] <== 558845607 * sbox[26][0].out + 1055005211 * sbox[26][1].out + 1277817208 * sbox[26][2].out;

    // round 27 [full]
    sbox[27][0] = SBoxAlpha();
    sbox[27][0].in <== state[27][0] + 1300540103;
    sbox[27][1] = SBoxAlpha();
    sbox[27][1].in <== state[27][1] + 921924081;
    sbox[27][2] = SBoxAlpha();
    sbox[27][2].in <== state[27][2] + 1002658919;
    state[28][0] <== 630515943 * sbox[27][0].out + 124443138 * sbox[27][1].out + 1067104518 * sbox[27][2].out;
    state[28][1] <== 914440123 * sbox[27][0].out + 229794830 * sbox[27][1].out + 704986396 * sbox[27][2].out;
    state[28][2] <== 558845607 * sbox[27][0].out + 1055005211 * sbox[27][1].out + 1277817208 * sbox[27][2].out;

    for (var i = 0; i < 3; i++) { out[i] <== state[28][i]; }
}

component main = Poseidon1T3_poseidon2_sparse();