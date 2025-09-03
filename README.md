# Tesbar

Projet open source de conception d'un eco system de modules permettant les choses suivantes :

- Module captant les trames CAN d'une Tesla et les envoyant en wifi vers d'autres modules
- Modules de réception pour :
    * Afficher sur une barre de leds le long du tableau de bord les évenements en provenance de la voiture : clignotant, présence de véhicule dans l'angle mort, alerte autopilote, ...
    * Afficher sur un afficheur LCD les informations du véhicule : vitesse, état de charge, odomètre, ...

## Motivation

 - Se familiariser avec les infomations CAN du véhicules et les exploiter.
 - Utiliser Copilot pour les développement en "vibe coding"
 - Développer un PCB pour l'émetteur
 - Développer un PCB pour le récepteur de barre led

## Matériel

Le matériel est composé principalement de modules Espressif.

- Emetteur
  - SoC : ESP32 ou ESP8266
  - CAN
    - CAN 1 : MCP2515 en SPI + transceiver
    - CAN 2 : twai + transceiver
- Récepteur
  - Soc : ESP32 ou ESP8266
- Barre led
  - Compatible WS2812
  - Provenance : Aliexpress
- Ecran LCD avec module ESP32 intégré et potentiellement charge sans fil
 - Provenance : Aliexpress

Le développement des PCB est fait avec KiCAD
- Site de fabrication : 

## Logiciel

- Framework Arduino
- Librairies open source
    - esp_now : broadcast des trames sur wifi
    - ota : mise à jour via wifi
    - [config](https://randomnerdtutorials.com/esp32-save-data-permanently-preferences/) : stockage en flash
    - ws2812fx : effet leds
    - mcp_can : pilotage du MCP2515 par SPI
    - [LVGL](https://developer.espressif.com/blog/making-the-fancy-user-interface-on-esp-has-never-been-easier/) : librarie graphique pour l'écran

## Barre de led

La barre de led est configurée via un fichier JSON téléchargé sur le module par wifi et associant segments de led, configuration des segments et evenements CAN associés

## Ecran LCD

L'écran rond recoit les informations du véhicule via le module émetteur et les affiche.

# Outils annexe

Outil de configuration et de génération du fichier JSON

## Références

Projets d'inspiration :
- Ref 1
- Ref 2