import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

// Painel de agentes: uma página com todas as assinaturas (inspirado no agents
// panel do Omarchy, MIT). Dados prontos vêm de backend.model (agents_usage/view.py).
Window {
    id: root
    // Congelado enquanto um nome é editado: recriar as linhas descartaria o texto digitado.
    property var model: backend.model
    property int editing: 0
    onEditingChanged: if (editing === 0) model = Qt.binding(() => backend.model)
    readonly property var geo: backend.geometry()
    property int selectedKey: 0
    property bool wasActive: false


    width: 440
    height: Math.min(content.implicitHeight + 2, geo.maxHeight)
    x: geo.right - width
    y: geo.top
    visible: true
    color: "transparent"
    flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    title: "agents-panel"  // casado pela regra for_window do i3

    // Fecha ao perder o foco (clicar fora), como um popup da barra.
    onActiveChanged: {
        if (active) wasActive = true
        else if (wasActive) Qt.quit()
    }
    Component.onCompleted: requestActivate()

    function selectedAccount() {
        for (const p of model.providers || [])
            for (const a of p.accounts)
                if (a.key === selectedKey && a.key > 0) return { provider: p, account: a }
        return null
    }

    Shortcut { sequence: "Esc"; onActivated: Qt.quit() }
    Shortcut { sequence: "R"; onActivated: backend.refresh() }
    Shortcut {
        sequences: ["Return", "Enter"]
        onActivated: {
            const s = selectedAccount()
            if (s && !s.account.active && !s.account.needs_signin)
                backend.useAccount(s.provider.id, s.account.id)
        }
    }
    Shortcut {
        sequence: "M"
        onActivated: {
            const s = selectedAccount()
            const p = s ? s.provider : (model.providers || [])[0]
            if (p && p.multi) backend.toggleMode(p.id)
        }
    }
    Item {
        focus: true
        Keys.onPressed: (event) => {
            if (event.key >= Qt.Key_1 && event.key <= Qt.Key_9) {
                root.selectedKey = event.key - Qt.Key_0
                event.accepted = true
            }
        }
    }

    Timer {
        interval: 1500
        running: screenshotPath !== ""
        onTriggered: frame.grabToImage(r => { r.saveToFile(screenshotPath); Qt.quit() })
    }

    Rectangle {
        id: frame
        anchors.fill: parent
        radius: 10
        color: theme.bg
        border.color: theme.border
        border.width: 1
        clip: true

        ColumnLayout {
            id: content
            anchors { left: parent.left; right: parent.right; top: parent.top }
            spacing: 0

            // ---------------------------------------------------- cabeçalho
            ColumnLayout {
                Layout.fillWidth: true
                Layout.margins: 14
                Layout.bottomMargin: 10
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "󰚩  Agentes"
                        color: theme.fg
                        font { family: theme.font; pixelSize: 15; bold: true }
                    }
                    Item { Layout.fillWidth: true }
                    IconButton {
                        glyph: backend.busy ? "" : ""
                        tip: "Atualizar agora (R)"
                        spinning: backend.busy
                        onClicked: backend.refresh()
                    }
                    IconButton { glyph: ""; tip: "Fechar (Esc)"; onClicked: Qt.quit() }
                }

                // Linha rotativa com o que foi usado em todas as contas
                Text {
                    id: tickerText
                    property int idx: 0
                    readonly property var lines: root.model.ticker || []
                    Layout.fillWidth: true
                    text: lines.length ? lines[idx % lines.length] : ""
                    color: theme.fgDim
                    elide: Text.ElideRight
                    font { family: theme.font; pixelSize: 12 }
                    Behavior on text {
                        SequentialAnimation {
                            NumberAnimation { target: tickerText; property: "opacity"; to: 0; duration: 150 }
                            PropertyAction {}
                            NumberAnimation { target: tickerText; property: "opacity"; to: 1; duration: 150 }
                        }
                    }
                    Timer {
                        interval: 4000; running: tickerText.lines.length > 1; repeat: true
                        onTriggered: tickerText.idx++
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: theme.border }

            // ---------------------------------------------------- providers
            Flickable {
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(providers.implicitHeight,
                                                 root.geo.maxHeight - 120)
                contentHeight: providers.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                ColumnLayout {
                    id: providers
                    width: parent.width
                    spacing: 0
                    Repeater {
                        model: root.model.providers || []
                        delegate: Agent {
                            Layout.fillWidth: true
                            provider: modelData
                            selectedKey: root.selectedKey
                            last: index === (root.model.providers || []).length - 1
                            onEditingChanged: {
                                if (editing) root.model = root.model  // quebra o binding: congela
                                root.editing += editing ? 1 : -1
                            }
                        }
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: theme.border }

            // ---------------------------------------------------- rodapé
            RowLayout {
                Layout.fillWidth: true
                Layout.margins: 10
                Layout.leftMargin: 14
                Layout.rightMargin: 14
                Text {
                    text: (root.model.outdated ? " " : "") + (root.model.updated_text || "")
                    color: root.model.outdated ? theme.orange : theme.fgDim
                    font { family: theme.font; pixelSize: 11 }
                }
                Item { Layout.fillWidth: true }
                Text {
                    text: "1-9 seleciona · Enter usa · M autoswitch"
                    color: theme.border
                    font { family: theme.font; pixelSize: 10 }
                }
            }
        }
    }

    component IconButton: AbstractButton {
        id: btn
        property string glyph
        property string tip
        property bool spinning: false
        implicitWidth: 26
        implicitHeight: 26
        hoverEnabled: true
        // Só o glifo gira; o fundo do hover fica parado.
        contentItem: Text {
            id: glyphText
            RotationAnimation on rotation {
                running: btn.spinning; from: 0; to: 360; duration: 900; loops: Animation.Infinite
                onRunningChanged: if (!running) glyphText.rotation = 0
            }
            text: btn.glyph
            color: btn.hovered ? theme.fg : theme.fgDim
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font { family: theme.font; pixelSize: 13 }
        }
        background: Rectangle { radius: 6; color: btn.hovered ? theme.bgSoft : "transparent" }
        ToolTip.visible: hovered && tip !== ""
        ToolTip.text: tip
        ToolTip.delay: 400
    }
}
