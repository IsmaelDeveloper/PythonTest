from aiortc import RTCPeerConnection


async def end_rtc_call(peer_connection: RTCPeerConnection):
    """
    Termine proprement une connexion RTC.
    :param peer_connection: L'objet RTCPeerConnection à fermer.
    """
    print("Enter end_rtc_call")

    # Vérifiez si la connexion est déjà fermée
    if peer_connection.connectionState == "closed":
        print("Peer connection already closed")
        return

    # Arrêtez toutes les pistes des senders

    for sender in peer_connection.getTransceivers():
        print("Enter getTransceivers")
        try:
            sender.stop()
            print("Track stopped")
        except Exception as e:
            print(f"Erreur lors de l'arrêt de la piste: {e}")

    for sender in peer_connection.getSenders():
        print("Enter getSenders")
        try:
            if sender.track:
                sender.track.stop()
                print("Track stopped")
        except Exception as e:
            print(f"Erreur lors de l'arrêt de la piste: {e}")

    print("finish getSenders")

    # Fermez la connexion RTC elle-même
    try:
        print("Enter close peer")
        await peer_connection.close()
        print("Peer connection closed")
    except Exception as e:
        print(f"Erreur lors de la fermeture de la connexion RTC: {e}")

    print("Exit end_rtc_call")
