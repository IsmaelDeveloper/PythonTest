import QtQuick 2.0
import QtQuick.Layouts 1.3

Item {  
    RowLayout { 
        spacing : 0 
        Image {
            
            id: dustButton
            source: "../images/bt_Dust.png"  
            // scale: 0.8
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
        // Image {
        //     id: weatherButton
        //     source: "../images/bt_weather.png" 
        //     // scale: 0.8
        //     width: weatherButton.sourceSize.width  
        //     height: weatherButton.sourceSize.height  
        //     MouseArea {
        //         anchors.fill: parent 
        //         onClicked: homeApp.weatherClicked()
        //         onEntered: weatherButton.source = "../images/bt_weather_hover.png"
        //         onExited: weatherButton.source = "../images/bt_weather.png"

        //     }
        // }
        Image {
            id: busButton
            source: "../images/bus_and_subway.png"  
            // scale: 0.8
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
            // scale: 0.8
            width: kiosButton.sourceSize.width  
            height: kiosButton.sourceSize.height
            MouseArea {
                anchors.fill: parent 
                onClicked: homeApp.kioskClicked()
                onEntered: kiosButton.source = "../images/kiosk_btn_hover.png"
                onExited: kiosButton.source = "../images/kiosk_btn.png"

            }
        }
        Image {
            id: callButton
            source: "../images/bt_call.png"  
            // scale: 0.8
            width: callButton.sourceSize.width 
            height: callButton.sourceSize.height 
            MouseArea {
                anchors.fill: parent 
                onClicked: homeApp.callClicked()
                onEntered: callButton.source = "../images/bt_call_hover.png"
                onExited: callButton.source = "../images/bt_call.png"

            }
        }
    }
}
