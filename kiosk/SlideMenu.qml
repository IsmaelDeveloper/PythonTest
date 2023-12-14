import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12

Item {
    id: slideMenu
    width: parent.width * 0.4 // 40% de la largeur de la fenêtre
    height: parent.height * 0.5 // Prend la moitié de la hauteur de la fenêtre
    x: parent.width // Position initiale à l'extérieur de l'écran

    // Animation de glissement
    Behavior on x {
        SpringAnimation {
            spring: 3
            damping: 0.2
        }
    }

    // Raccourci pour la touche F3
    Shortcut {
        sequence: "F3"
        onActivated: {
            print("F3 pressed")
            slideMenu.x = slideMenu.x === parent.width ? parent.width - slideMenu.width : parent.width
        }
    }

    // Structure du menu
    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        // Onglets
        TabBar {
            Layout.fillWidth: true
            TabButton { text: "Onglet 1" }
            TabButton { text: "Onglet 2" }
        }

        // Contenu des onglets
        StackLayout {
            id: stackLayout
            Layout.fillWidth: true
            Layout.fillHeight: true

            Item {
                // Contenu de l'onglet 1
            }

            Item {
                // Contenu de l'onglet 2
            }
        }
    }
}
