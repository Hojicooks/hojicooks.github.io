# Cabine Miroir

Miroir selfie avec retardateur, dressing détaillé (marque, taille, matière, prix, saisons, style, lien boutique, notes) et cabine d'essayage IA pour composer une tenue complète : haut, bas et chaussures, avec un cadenas par pièce.

Site : https://hojicooks.github.io

## Moteurs (démos gratuites Hugging Face)

- Haut et veste : IDM-VTON (yisol/IDM-VTON)
- Bas et robe : OOTDiffusion (levihsu/OOTDiffusion)
- Chaussures et mode « Réaliste » : Qwen Image Edit 2509 (Qwen/Qwen-Image-Edit-2509)

Les pièces s'appliquent dans l'ordre bas, chaussures, haut ; chaque étape est gardée, donc changer seulement le haut ne coûte qu'une génération.

## Données

Photos, dressing et looks restent dans le téléphone (IndexedDB). Un rendu envoie la photo choisie et les vêtements concernés à la démo publique qui les traite.
