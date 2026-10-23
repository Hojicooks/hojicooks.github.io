# Cabine Miroir

Miroir selfie avec coach de cadrage, dressing détaillé (marque, taille, matière, prix, saisons, style, lien boutique, notes) et cabine d'essayage IA pour composer une tenue complète : haut, bas et chaussures, avec un cadenas par pièce.

Site : https://hojicooks.github.io

## Fonctions

- **Miroir** : « Direct IA » (Decart Lucy VTON 3.6, payant au temps : clé dans les réglages, jeton de courte durée limité au site ; rien n'est facturé au démarrage : l'app attend de te voir en entier une seconde, lance le retardateur, puis se connecte ; arrêt en levant les deux mains une seconde, 3 s après ta sortie de l'image ou à la durée maximale ; image envoyée à la verticale quand le téléphone est droit, recadrée en 9:16 même si la caméra filme en paysage ; une vidéo enregistrée par tenue essayée et rangée dans les Looks et sur les fiches), effet filtre en direct (les pièces détourées de tes tenues suivent ton corps, gratuit, dans le téléphone) avec changement de tenue d'un balayage de la main (une seule main suivie, retour de la main ignoré, grande flèche de confirmation, tenue envoyée au Direct IA une demi-seconde après le dernier geste), retardateur avec bips, coach de cadrage en direct (MediaPipe Pose, dans le téléphone), déclenchement en levant la main, plein écran, lumière d'appoint, repères, grille, effet miroir désactivable, rafale de 3 photos. La photo reprend exactement le cadrage affiché (verticale même si la caméra filme en paysage).
- **Dressing** : tenues complètes (haut, bas, chaussures) créées à la main, depuis la cabine ou reprises des looks ; photo du devant et du dos, fond retiré ou fond blanc par une IA de détourage dans le téléphone (RMBG-1.4 de Bria via Transformers.js, usage non commercial ; détourage simple par couleur si l'IA ne se charge pas), catégorie et couleur devinées à l'import, tri (récents, favoris, couleur, plus ou moins portés), 2 à 4 vignettes par ligne, statistiques (valeur, pièces jamais portées, coût par port).
- **Cabine** : essai de dos (photo de toi de dos + photo du dos des vêtements), « Inspire-moi » propose une tenue selon la saison ou la météo du jour (Open-Meteo), l'accord des couleurs, les favoris et les pièces peu portées, en gardant les pièces verrouillées ; indicateur d'harmonie ; aperçu à plat instantané, sans IA.
- **Looks** : « Porté aujourd'hui », favoris, renommage, filtres (favoris, portés, IA, à plat), comparaison, partage.
- **Confort** : suppression annulable 5 s, guide de démarrage, aide selon l'écran, thème sombre, clair ou auto, couleur d'accent, texte agrandi, sauvegarde et restauration (fichier JSON).

## Moteurs (démos gratuites Hugging Face)

- Haut et veste : IDM-VTON (yisol/IDM-VTON), secours FitDiT puis Leffa
- Bas et robe : FitDiT (BoyuanJiang/FitDiT), secours Leffa (franciszzj/Leffa)
- Chaussures et mode « Réaliste » : Qwen Image Edit 2511 rapide (prithivMLmods/Qwen-Image-Edit-2511-LoRAs-Fast)

Client Gradio : @gradio/client 1.19.1 pour IDM-VTON (Gradio 4), 2.7.1 pour les autres (Gradio 5 et 6).

Quota ZeroGPU : sans compte, 2 min de calcul par jour et chaque appel réserve au moins 60 s ; Leffa réserve 180 s et n'est donc utilisé qu'avec un jeton. Avec un jeton gratuit : 5 min par jour et une file prioritaire.

Les pièces s'appliquent dans l'ordre bas, chaussures, haut ; chaque étape est gardée. Si une démo est en pause, plante ou ne répond plus pendant 2 min 30, la suivante prend le relais. La photo garde son cadrage d'origine, et l'app vérifie dans le téléphone (MediaPipe Pose) que les jambes et les pieds sont visibles.

## Données

Photos, dressing et looks restent dans le téléphone (IndexedDB). Un rendu envoie la photo choisie et les vêtements concernés à la démo publique qui les traite. La météo n'envoie que la ville (ou une position arrondie) à Open-Meteo. Les bibliothèques et le modèle de détection du corps sont gardés en cache après le premier chargement.
