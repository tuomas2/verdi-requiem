<?xml version="1.0" encoding="UTF-8"?>
<museScore version="4.00">
  <Style>
    <createMultiMeasureRests>1</createMultiMeasureRests>
    <minEmptyMeasures>2</minEmptyMeasures>
    <minMMRestWidth>4</minMMRestWidth>
    <!-- Tahtinumero jokaiseen tahtiin, ei vain rivin alkuun: laulaja etsii
         harjoituksissa yksittäisen tahdin, ja rivin alusta laskeminen on
         hidasta ja menee helposti yhden pieleen. -->
    <showMeasureNumber>1</showMeasureNumber>
    <showMeasureNumberOne>1</showMeasureNumberOne>
    <measureNumberSystem>0</measureNumberSystem>
    <measureNumberInterval>1</measureNumberInterval>
    <!-- Taukopalkin päälle sen tahtiväli ("47-52"), jotta myös tiivistetyn
         tauon yli näkee, mistä tahdista lauluosuus jatkuu. -->
    <mmRestShowMeasureNumberRange>1</mmRestShowMeasureNumberRange>
    <!-- Väljyyttä nuottirivien väliin käsimerkinnöille. Oletus on 5,0 ja
         antaa rivinvälin 25,1 mm (10 riviä sivulle); 11,5 antaa 29,3 mm
         (9 riviä) ja 13,0 antaa 33,7 mm (8 riviä). Arvo on portaittainen:
         se ratkaisee montako riviä sivulle mahtuu, ja loput tilasta jaetaan
         tasan, joten väliarvot eivät tuota väliarvoja. Hinta 11,5:stä on
         kaksi sivua stemmaa kohti (B I 14 -> 16). Huom: pelkkä
         minSystemDistance ei tee tässä mitään — mitattu, ei arvattu. -->
    <minSystemSpread>11.5</minSystemSpread>
  </Style>
</museScore>
