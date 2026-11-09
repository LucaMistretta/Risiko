/**
 * Carte territorio stile Risiko: armi (Fante, Cannone, Cavaliere) + silhouette.
 * Espone window.CarteTerritorioRisiko per mini-risiko.html.
 */
(function () {
    'use strict';

    const cacheSilhouette = {};

    const PERCORSI_ARMI = {
        Fante: 'armi/fante.jpg',
        Cavaliere: 'armi/cavaliere.jpg',
        Cannone: 'armi/cannone.jpg'
    };

    function iconaArmaHtml(simbolo) {
        if (simbolo === 'Jolly') {
            return `
                <div class="carta-risiko-armi-jolly">
                    <img src="${PERCORSI_ARMI.Fante}" alt="Fante">
                    <img src="${PERCORSI_ARMI.Cavaliere}" alt="Cavaliere">
                    <img src="${PERCORSI_ARMI.Cannone}" alt="Cannone">
                </div>`;
        }
        const percorso = PERCORSI_ARMI[simbolo] || PERCORSI_ARMI.Fante;
        return `<img class="carta-risiko-arma-img" src="${percorso}" alt="${simbolo}">`;
    }

    function slugTerritorio(nome) {
        return String(nome)
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    async function ottieniSilhouette(nomeTerritorio) {
        if (nomeTerritorio === 'Jolly' || nomeTerritorio === '?') {
            return null;
        }
        const slug = slugTerritorio(nomeTerritorio);
        if (cacheSilhouette[slug]) {
            return cacheSilhouette[slug];
        }
        try {
            const risposta = await fetch(`territori/${slug}.svg`);
            if (!risposta.ok) {
                return null;
            }
            const testo = await risposta.text();
            const documento = new DOMParser().parseFromString(testo, 'image/svg+xml');
            const svg = documento.querySelector('svg');
            const percorsi = Array.from(documento.querySelectorAll('path'))
                .map((path) => path.getAttribute('d'))
                .filter(Boolean);
            const viewBox = svg ? svg.getAttribute('viewBox') || '0 0 100 100' : '0 0 100 100';
            cacheSilhouette[slug] = { viewBox, percorsi };
            return cacheSilhouette[slug];
        } catch (errore) {
            console.warn('Silhouette non caricata:', nomeTerritorio, errore);
            return null;
        }
    }

    function htmlSilhouetteSincrono(nomeTerritorio) {
        if (nomeTerritorio === 'Jolly') {
            return `
                <div class="carta-risiko-jolly-fondo">
                    <div class="carta-risiko-jolly-titolo">RISIKO</div>
                    <div class="carta-risiko-jolly-sottotitolo">Territori</div>
                    <img class="carta-risiko-arma-img" src="${PERCORSI_ARMI.Cannone}" alt="Cannone">
                </div>`;
        }
        const slug = slugTerritorio(nomeTerritorio);
        // Usa direttamente l'SVG del territorio (niente fetch): sulla carta diventa nero stile Risiko
        return `<img class="carta-risiko-silhouette-img" src="territori/${slug}.svg" alt="Mappa ${nomeTerritorio}" loading="lazy">`;
    }

    /**
     * Genera HTML di una carta stile Risiko.
     * @param {{nome:string,simbolo:string}} carta
     * @param {{indice?:number|null, selezionabile?:boolean, dimensione?:string, classeExtra?:string}} opzioni
     */
    function htmlCarta(carta, opzioni = {}) {
        const nome = carta.nome || '?';
        const simbolo = carta.simbolo || 'Fante';
        const indice = opzioni.indice;
        const selezionabile = opzioni.selezionabile === true;
        const dimensione = opzioni.dimensione || 'normale';
        const classeExtra = opzioni.classeExtra || '';
        const classeSimbolo = String(simbolo).toLowerCase();
        const attrIndice = indice === undefined || indice === null ? '' : ` data-carta-indice="${indice}"`;
        const classeCarta = selezionabile ? 'carta carta-risiko' : 'carta-risiko';

        return `
            <div class="${classeCarta} ${classeSimbolo} dim-${dimensione} ${classeExtra}"${attrIndice} title="${nome} — ${simbolo}">
                <div class="carta-risiko-arma">${iconaArmaHtml(simbolo)}</div>
                <div class="carta-risiko-nome">${nome}</div>
                <div class="carta-risiko-mappa">${htmlSilhouetteSincrono(nome)}</div>
            </div>`;
    }

    async function precarica(listaNomiTerritori) {
        const nomi = listaNomiTerritori || [];
        await Promise.all(nomi.map((nome) => ottieniSilhouette(nome)));
    }

    function assicuratiOverlay() {
        let overlay = document.getElementById('overlay-carta-territorio');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'overlay-carta-territorio';
            overlay.className = 'overlay-carta-territorio';
            overlay.innerHTML = `
                <div class="overlay-carta-box" role="dialog" aria-modal="true">
                    <p class="overlay-carta-messaggio" id="overlay-carta-messaggio"></p>
                    <div id="overlay-carta-contenuto"></div>
                    <button type="button" class="overlay-carta-chiudi" id="overlay-carta-chiudi">Continua</button>
                </div>`;
            document.body.appendChild(overlay);
            overlay.addEventListener('click', (evento) => {
                if (evento.target === overlay) {
                    nascondiPopupCarta();
                }
            });
            document.getElementById('overlay-carta-chiudi').addEventListener('click', nascondiPopupCarta);
        }

        let galleria = document.getElementById('overlay-galleria-carte');
        if (!galleria) {
            galleria = document.createElement('div');
            galleria.id = 'overlay-galleria-carte';
            galleria.className = 'overlay-galleria-carte';
            galleria.innerHTML = `
                <div class="galleria-carte-box" role="dialog" aria-modal="true" aria-label="Mazzo carte territorio">
                    <div class="galleria-carte-testata">
                        <h2>Mazzo carte territorio (44)</h2>
                        <button type="button" id="galleria-carte-chiudi" aria-label="Chiudi">×</button>
                    </div>
                    <p class="galleria-carte-nota">42 territori + 2 Jolly — Fante, Cavaliere, Cannone</p>
                    <div class="galleria-carte-griglia" id="galleria-carte-griglia"></div>
                </div>`;
            document.body.appendChild(galleria);
            galleria.addEventListener('click', (evento) => {
                if (evento.target === galleria) {
                    nascondiGalleria();
                }
            });
            document.getElementById('galleria-carte-chiudi').addEventListener('click', nascondiGalleria);
        }
    }

    /** Timer chiusura automatica del popup carta (allineato ai dialoghi di gioco). */
    let timerChiusuraPopupCarta = null;
    const MILLISECONDI_CHIUSURA_AUTOMATICA_POPUP_CARTA = 1300;

    function annullaTimerChiusuraPopupCarta() {
        if (timerChiusuraPopupCarta !== null) {
            clearTimeout(timerChiusuraPopupCarta);
            timerChiusuraPopupCarta = null;
        }
    }

    async function mostraPopupCarta(carta, messaggio) {
        assicuratiOverlay();
        if (carta && carta.nome && carta.nome !== 'Jolly') {
            await ottieniSilhouette(carta.nome);
        }
        const overlay = document.getElementById('overlay-carta-territorio');
        document.getElementById('overlay-carta-messaggio').textContent = messaggio || '';
        document.getElementById('overlay-carta-contenuto').innerHTML = htmlCarta(carta, {
            dimensione: 'grande',
            selezionabile: false
        });
        overlay.classList.add('visibile');
        annullaTimerChiusuraPopupCarta();
        timerChiusuraPopupCarta = setTimeout(() => {
            nascondiPopupCarta();
        }, MILLISECONDI_CHIUSURA_AUTOMATICA_POPUP_CARTA);
    }

    function nascondiPopupCarta() {
        annullaTimerChiusuraPopupCarta();
        const overlay = document.getElementById('overlay-carta-territorio');
        if (overlay) {
            overlay.classList.remove('visibile');
        }
    }

    async function mostraGalleria(listaCarte) {
        assicuratiOverlay();
        const nomi = listaCarte
            .map((carta) => carta.nome)
            .filter((nome) => nome && nome !== 'Jolly');
        await precarica(nomi);

        const griglia = document.getElementById('galleria-carte-griglia');
        griglia.innerHTML = listaCarte
            .map((carta) => htmlCarta(carta, { dimensione: 'media', selezionabile: false }))
            .join('');
        document.getElementById('overlay-galleria-carte').classList.add('visibile');
    }

    function nascondiGalleria() {
        const galleria = document.getElementById('overlay-galleria-carte');
        if (galleria) {
            galleria.classList.remove('visibile');
        }
    }

    window.CarteTerritorioRisiko = {
        htmlCarta,
        precarica,
        ottieniSilhouette,
        mostraPopupCarta,
        nascondiPopupCarta,
        mostraGalleria,
        nascondiGalleria,
        assicuratiOverlay,
        slugTerritorio
    };
})();
