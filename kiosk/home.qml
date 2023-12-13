import QtQuick 2.0
import QtQuick.Layouts 1.3

Item { 
    RowLayout { 
        Image {
            id: dustButton
            source: "./ressources/images/bt_Dust.png"  
            width: dustButton.sourceSize.width    
            height: dustButton.sourceSize.height  
            MouseArea {
                anchors.fill: parent 
                onClicked: homeApp.dustClicked()
                onEntered: dustButton.source = "./ressources/images/bt_dust_hover.png"
                onExited: dustButton.source = "./ressources/images/bt_Dust.png"
            }
            Layout.alignment: Qt.AlignLeft
            Layout.leftMargin: 50
        }
        Image {
            id: weatherButton
            source: "./ressources/images/bt_weather.png"  
            width: weatherButton.sourceSize.width    
            height: weatherButton.sourceSize.height  
            MouseArea {
                anchors.fill: parent 
                onClicked: homeApp.weatherClicked()
                onEntered: weatherButton.source = "./ressources/images/bt_weather_hover.png"
                onExited: weatherButton.source = "./ressources/images/bt_weather.png"

            }
        }
        Image {
            id: busButton
            source: "./ressources/images/bus_and_subway.png"  
            width: busButton.sourceSize.width    
            height: busButton.sourceSize.height  
            MouseArea {
                anchors.fill: parent 
                onClicked: homeApp.busClicked()
                onEntered: busButton.source = "./ressources/images/bus_and_subway_hover.png"
                onExited: busButton.source = "./ressources/images/bus_and_subway.png"

            }
        }
        Image {
            id: kiosButton
            source: "./ressources/images/kiosk_btn.png"  
            width: kiosButton.sourceSize.width    
            height: kiosButton.sourceSize.height  
            MouseArea {
                anchors.fill: parent 
                onClicked: homeApp.kioskClicked()
                onEntered: kiosButton.source = "./ressources/images/kiosk_btn_hover.png"
                onExited: kiosButton.source = "./ressources/images/kiosk_btn.png"

            }
        }
    }
}
