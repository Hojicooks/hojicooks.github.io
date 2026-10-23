# Cabine Miroir

Miroir selfie avec retardateur, dressing détaillé (marque, taille, matière, prix, saisons, style, lien boutique, notes) et cabine d'essayage IA pour composer une tenue complète : haut, bas et chaussures, avec un cadenas par pièce.

Site : https://hojicooks.github.io

## Moteurs (démos gratuites Hugging Face)

- Haut et veste : IDM-VTON (yisol/IDM-VTON), secours FitDiT puis Leffa
- Bas et robe : FitDiT (BoyuanJiang/FitDiT), secours Leffa (franciszzj/Leffa)
- Chaussures et mode « Réaliste » : Qwen Image Edit 2511, version rapide (linoyts/Qwen-Image-Edit-2511-Fast)

Les pièces s'appliquent dans l'ordre bas, chaussures, haut ; chaque étape est gardée, donc changer seulement le haut ne coûte qu'une génération. Si une démo est en pause ou plante, la suivante prend le relais. La photo garde son cadrage d'origine (rien n'est recoupé), et l'app vérifie dans le téléphone (MediaPipe Pose) que les jambes et les pieds sont visibles avant d'essayer un bas ou des chaussures.

## Données

Photos, dressing et looks restent dans le téléphone (IndexedDB). Un rendu envoie la photo choisie et les vêtements concernés à la démo publique qui les traite.
