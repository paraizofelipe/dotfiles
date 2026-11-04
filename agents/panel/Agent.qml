import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Seção de um provider: contas com medidores (ou saldo), Use/Autoswitch e "+".
ColumnLayout {
    id: section
    property var provider: ({ id: "", name: "", accounts: [] })
    property int selectedKey: 0
    property bool last: false
    property bool adding: false
    spacing: 6

    // ---------------------------------------------------- título do provider
    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 12
        Layout.leftMargin: 14
        Layout.rightMargin: 10
        spacing: 7
        // Logo do provider (icons/<id>.svg, ver icons/README.md)
        Image {
            source: section.provider.id ? Qt.resolvedUrl("icons/" + section.provider.id + ".svg") : ""
            sourceSize { width: 14; height: 14 }
            Layout.preferredWidth: 14
            Layout.preferredHeight: 14
        }
        Text {
            text: section.provider.name.toUpperCase()
            color: theme.accent
            font { family: theme.font; pixelSize: 11; bold: true; letterSpacing: 1 }
        }
        Item { Layout.fillWidth: true }
        Chip {
            visible: section.provider.multi && section.provider.accounts.length > 1
            label: section.provider.mode === "auto" ? " Autoswitch" : " Avisar"
            on: section.provider.mode === "auto"
            tip: section.provider.mode === "auto"
                 ? "Troca sozinho ao passar de " + section.provider.threshold + "% (M)"
                 : "Avisa ao passar de " + section.provider.threshold + "% (M)"
            onClicked: backend.toggleMode(section.provider.id)
        }
        Chip {
            visible: section.provider.multi
            label: ""
            tip: "Adicionar assinatura"
            onClicked: { section.adding = true; newName.forceActiveFocus() }
        }
    }

    // ---------------------------------------------------- nova conta
    TextField {
        id: newName
        visible: section.adding
        Layout.fillWidth: true
        Layout.leftMargin: 14
        Layout.rightMargin: 14
        placeholderText: "Nome da conta (ex.: Work) e Enter"
        color: theme.fg
        placeholderTextColor: theme.fgDim
        font { family: theme.font; pixelSize: 12 }
        background: Rectangle { radius: 6; color: theme.bgSoft; border.color: theme.accent }
        onAccepted: { backend.addAccount(section.provider.id, text); section.adding = false; text = "" }
        Keys.onEscapePressed: { section.adding = false; text = "" }
    }

    // ---------------------------------------------------- contas
    Repeater {
        model: section.provider.accounts
        delegate: Rectangle {
            id: row
            required property var modelData
            readonly property var acc: modelData
            readonly property bool selected: acc.key > 0 && acc.key === section.selectedKey
            Layout.fillWidth: true
            Layout.leftMargin: 8
            Layout.rightMargin: 8
            implicitHeight: rowCol.implicitHeight + 14
            radius: 8
            color: selected ? theme.bgSoft : (hover.hovered ? theme.bgAlt : "transparent")
            border.color: acc.active && section.provider.accounts.length > 1 ? theme.border : "transparent"
            HoverHandler { id: hover }

            ColumnLayout {
                id: rowCol
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 7; leftMargin: 8 }
                spacing: 5

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        visible: row.acc.key > 0
                        text: row.acc.key
                        color: theme.fgDim
                        font { family: theme.font; pixelSize: 11 }
                    }
                    Text {
                        visible: row.acc.active && section.provider.accounts.length > 1
                        text: ""
                        color: "#b8bb26"
                        font { family: theme.font; pixelSize: 7 }
                    }
                    // Clique no nome para renomear
                    Text {
                        id: nameText
                        visible: !nameEdit.visible
                        text: row.acc.label
                        color: theme.fg
                        font { family: theme.font; pixelSize: 13; bold: row.acc.active }
                        MouseArea {
                            anchors.fill: parent
                            enabled: section.provider.multi
                            cursorShape: section.provider.multi ? Qt.IBeamCursor : Qt.ArrowCursor
                            onClicked: { nameEdit.text = row.acc.label; nameEdit.visible = true; nameEdit.forceActiveFocus() }
                        }
                    }
                    TextField {
                        id: nameEdit
                        visible: false
                        Layout.preferredWidth: 140
                        color: theme.fg
                        font { family: theme.font; pixelSize: 12 }
                        background: Rectangle { radius: 4; color: theme.bgSoft; border.color: theme.accent }
                        onAccepted: { backend.renameAccount(section.provider.id, row.acc.id, text); visible = false }
                        Keys.onEscapePressed: visible = false
                        onActiveFocusChanged: if (!activeFocus) visible = false
                    }
                    Text {
                        visible: row.acc.plan !== ""
                        text: row.acc.plan
                        color: theme.bg
                        font { family: theme.font; pixelSize: 9; bold: true }
                        leftPadding: 5; rightPadding: 5; topPadding: 1; bottomPadding: 1
                        Rectangle { anchors.fill: parent; z: -1; radius: 3; color: theme.fgDim }
                    }
                    Item { Layout.fillWidth: true }
                    Chip {
                        visible: row.acc.needs_signin
                        label: " Entrar"
                        warn: true
                        tip: "Abre um terminal para refazer o login desta conta"
                        onClicked: backend.login(section.provider.id, row.acc.id)
                    }
                    Chip {
                        visible: section.provider.multi && !row.acc.active && !row.acc.needs_signin
                        label: "Usar"
                        tip: "Novas sessões passam a usar esta conta (" + row.acc.key + " + Enter)"
                        onClicked: backend.useAccount(section.provider.id, row.acc.id)
                    }
                }

                Text {
                    visible: row.acc.status_text !== ""
                    Layout.fillWidth: true
                    text: row.acc.status_text
                    color: row.acc.needs_signin ? theme.orange : theme.fgDim
                    elide: Text.ElideRight
                    font { family: theme.font; pixelSize: 11; italic: true }
                }

                Repeater {
                    model: row.acc.meters
                    delegate: Meter { Layout.fillWidth: true; meter: modelData }
                }

                // Saldo pré-pago (OpenRouter / créditos)
                RowLayout {
                    visible: row.acc.balance !== null && row.acc.balance !== undefined
                    Layout.fillWidth: true
                    spacing: 8
                    Bar {
                        Layout.fillWidth: true
                        fraction: row.acc.balance ? row.acc.balance.fraction : 0
                        barColor: theme.accent
                    }
                    Text {
                        text: row.acc.balance ? row.acc.balance.text : ""
                        color: theme.fg
                        font { family: theme.font; pixelSize: 11 }
                    }
                }
            }
        }
    }

    Rectangle {
        visible: !section.last
        Layout.fillWidth: true
        Layout.topMargin: 6
        Layout.leftMargin: 14
        Layout.rightMargin: 14
        height: 1
        color: theme.bgSoft
    }
    Item { visible: section.last; implicitHeight: 6 }

    // ---------------------------------------------------- componentes
    component Bar: Rectangle {
        property real fraction: 0
        property color barColor: theme.accent
        implicitHeight: 6
        radius: 3
        color: theme.bgSoft
        Rectangle {
            width: Math.max(parent.radius * 2 * (parent.fraction > 0), parent.width * parent.fraction)
            height: parent.height
            radius: parent.radius
            color: parent.barColor
            Behavior on width { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
        }
    }

    component Meter: RowLayout {
        id: m
        property var meter: ({})
        spacing: 8
        Text {
            text: m.meter.label
            color: theme.fgDim
            Layout.preferredWidth: 52
            font { family: theme.font; pixelSize: 11 }
        }
        Bar {
            Layout.fillWidth: true
            fraction: m.meter.fraction
            barColor: m.meter.color
            HoverHandler { id: barHover }
            ToolTip.visible: barHover.hovered
            ToolTip.text: m.meter.percent + "% usado · " + m.meter.pace_text
        }
        Text {
            text: m.meter.percent_text
            color: m.meter.color
            horizontalAlignment: Text.AlignRight
            Layout.preferredWidth: 34
            font { family: theme.font; pixelSize: 11; bold: true }
        }
        Text {
            text: m.meter.reset_text
            color: theme.fgDim
            Layout.preferredWidth: 118
            font { family: theme.font; pixelSize: 10 }
        }
    }

    component Chip: AbstractButton {
        id: chip
        property string label
        property string tip
        property bool on: false
        property bool warn: false
        hoverEnabled: true
        implicitHeight: 22
        implicitWidth: chipText.implicitWidth + 16
        contentItem: Text {
            id: chipText
            text: chip.label
            color: chip.warn ? theme.orange : (chip.on ? theme.bg : theme.fg)
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font { family: theme.font; pixelSize: 11 }
        }
        background: Rectangle {
            radius: 11
            color: chip.on ? theme.accent : (chip.hovered ? theme.bgSoft : "transparent")
            border.color: chip.warn ? theme.orange : theme.border
        }
        ToolTip.visible: hovered && tip !== ""
        ToolTip.text: tip
        ToolTip.delay: 400
    }
}
