# Cabine Miroir

Miroir selfie avec retardateur, dressing détaillé (marque, taille, matière, prix, saisons, style, lien boutique, notes) et cabine d'essayage IA pour composer une tenue complète : haut, bas et chaussures, avec un cadenas par pièce.

Site : https://hojicooks.github.io

## Moteurs (démos gratuites Hugging Face)

- Haut et veste : IDM-VTON (yisol/IDM-VTON), secours FitDiT puis Leffa
- Bas et robe : FitDiT (BoyuanJiang/FitDiT), secours Leffa (franciszzj/Leffa)
- Chaussures et mode « Réaliste » : Qwen Image Edit 2511 rapide (prithivMLmods/Qwen-Image-Edit-2511-LoRAs-Fast)

Client Gradio : @gradio/client 1.19.1 pour IDM-VTON (Gradio 4), 2.7.1 pour les autres (Gradio 5 et 6).

Quota ZeroGPU : sans compte, 2 min de calcul par jour et chaque appel réserve au moins 60 s ; Leffa réserve 180 s et n'est donc utilisé qu'avec un jeton. Avec un jeton gratuit : 5 min par jour et une file prioritaire.

Les pièces s'appliquent dans l'ordre bas, chaussures, haut ; chaque étape est gardée. Si une démo est en pause, plante ou ne répond plus pendant 2 min 30, la suivante prend le relais. La photo garde son cadrage d'origine, et l'app vérifie dans le téléphone (MediaPipe Pose) que les jambes et les pieds sont visibles.

## Données

Photos, dressing et looks restent dans le téléphone (IndexedDB). Un rendu envoie la photo choisie et les vêtements concernés à la démo publique qui les traite.
