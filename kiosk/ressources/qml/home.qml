import QtQuick 2.0
import QtQuick.Layouts 1.3

Item { 
    RowLayout { 
        Image {
            id: dustButton
            source: "../images/bt_Dust.png"  
            width: dustButton.sourceSize.width    
            height: dustButton.sourceSize.height  
            MouseArea {
                anchors.fill: parent 
                onClicked: homeApp.dustClicked()
                onEntered: dustButton.source = "../images/bt_dust_hover.png"
                onExited: dustButton.source = "../images/bt_Dust.png"
            }
            Layout.alignment: Qt.AlignLeft
            Layout.leftMargin: 50
        }
        Image {
            id: weatherButton
            source: "../images/bt_weather.png"  
            width: weatherButton.sourceSize.width    
            height: weatherButton.sourceSize.height  
            MouseArea {
                anchors.fill: parent 
                onClicked: homeApp.weatherClicked()
                onEntered: weatherButton.source = "../images/bt_weather_hover.png"
                onExited: weatherButton.source = "../images/bt_weather.png"

            }
        }
        Image {
            id: busButton
            source: "../images/bus_and_subway.png"  
            width: busButton.sourceSize.width    
            height: busButton.sourceSize.height  
            MouseArea {
                anchors.fill: parent 
                onClicked: homeApp.busClicked()
                onEntered: busButton.source = "../images/bus_and_subway_hover.png"
                onExited: busButton.source = "../images/bus_and_subway.png"

            }
        }
        Image {
            id: kiosButton
            source: "../images/kiosk_btn.png"  
            width: kiosButton.sourceSize.width    
            height: kiosButton.sourceSize.height  
            MouseArea {
                anchors.fill: parent 
                onClicked: homeApp.kioskClicked()
                onEntered: kiosButton.source = "../images/kiosk_btn_hover.png"
                onExited: kiosButton.source = "../images/kiosk_btn.png"

            }
        }
    }
}
