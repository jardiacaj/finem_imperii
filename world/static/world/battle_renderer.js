function BattleRenderer(battle_data) {

    var zis = this;

    /* VARS */

    zis.organizations = battle_data.organizations;
    zis.characters = battle_data.characters;
    zis.units = battle_data.units;
    zis.contubernia = battle_data.contubernia;


    /* CONSTRUCTION */
    zis.renderer = new BaseRenderer();

    zis.renderer.render();
    $(document).on('click', zis.mouse_click_listener_notifier);

}
