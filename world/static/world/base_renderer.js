function BaseRenderer() {

    var zis = this;

    zis.init_camera = function () {
        zis.camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        zis.camera.position.z = 2.5;
        zis.camera.position.x = 2.5;
        zis.camera.position.y = 12;
        zis.camera.lookAt(new THREE.Vector3( 0, 0, 0 ));
        zis.camera.aspect = window.innerWidth / window.innerHeight;
        zis.camera.updateProjectionMatrix();
    };

    zis.init_renderer = function () {
        zis.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        zis.renderer.setSize(window.innerWidth, window.innerHeight);
        zis.renderer.setClearColor( 0xffffff, 0);
    };

    zis.add_orbit_controls = function () {
        zis.controls = new THREE.OrbitControls(zis.camera, zis.renderer.domElement);
        zis.controls.addEventListener( 'change', zis.render );
    };

    zis.init_lighting = function () {
        zis.ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
        zis.scene.add(zis.ambientLight);
        zis.directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        zis.directionalLight.position.set(1, 1, 1).normalize();
        zis.scene.add(zis.directionalLight);
    };

    zis.mouse_move_listener = function (event) {
        // it's pointless to do anything if there are no callbacks set
        if(zis.region_callback === undefined && zis.settlement_callback === undefined && zis.click_callback === undefined)
            return;
        // calculate mouse position in normalized device coordinates
        // (-1 to +1) for both components
        zis.mouse_vector.x = (event.clientX / window.innerWidth ) * 2 - 1;
        zis.mouse_vector.y = - (event.clientY / window.innerHeight) * 2 + 1;
        zis.pick();
    };

    zis.window_resize_listener = function (event) {
        zis.camera.aspect = window.innerWidth / window.innerHeight;
        zis.camera.updateProjectionMatrix();
        zis.renderer.setSize( window.innerWidth, window.innerHeight );
        zis.render();
        if(zis.region_tags_enabled) zis.rerender_region_tags();
        if(zis.settlement_tags_enabled) zis.rerender_settlement_tags();
        zis.pick();
    };

    zis.mouse_click_listener_notifier = function (event) {
        if (zis.click_callback !== undefined) {
            return zis.click_callback(zis.picked_region, zis.picked_settlement);
        }
    };

    zis.notify_region_pick = function (region) {
        if (region !== zis.picked_region) {
            zis.picked_region = region;
            if (zis.region_callback !== undefined) return zis.region_callback(region);
        }
    };

    zis.notify_settlement_pick = function (settlement) {
        if (settlement !== zis.picked_settlement) {
            zis.picked_settlement = settlement;
            if (zis.settlement_callback !== undefined) return zis.settlement_callback(settlement);
        }
    };

    zis.pick = function () {
        zis.raycaster.setFromCamera( zis.mouse_vector, zis.camera );

        // calculate objects intersecting the picking ray
        var intersects = zis.raycaster.intersectObjects( zis.scene.children );
        var region_intersected = false;
        var settlement_intersected = false;

        // notify only the first intersected element
        for ( var i = 0; i < intersects.length; i++ ) {

            var region = intersects[ i ].object.region;
            if (region !== undefined && !region_intersected) {
                zis.notify_region_pick(region);
                region_intersected = true;
            }
            var settlement = intersects[ i ].object.settlement;
            if (settlement !== undefined && !settlement_intersected) {
                zis.notify_settlement_pick(settlement);
                settlement_intersected = true;
            }

        }

        if (!settlement_intersected) zis.notify_settlement_pick(undefined);
        if (!region_intersected) zis.notify_region_pick(undefined);
    };

    zis.render = function () {
        zis.renderer.render(zis.scene, zis.camera);
    };

    zis.canvas_container = document.createElement( 'div' );
    document.body.appendChild( zis.canvas_container );

    zis.scene = new THREE.Scene();
    zis.init_camera();
    zis.init_renderer();
    zis.init_lighting();
    zis.raycaster = new THREE.Raycaster();
    zis.mouse_vector = new THREE.Vector2();

    zis.canvas_container.appendChild(zis.renderer.domElement);

    $(window).on('resize', zis.window_resize_listener);
    $(document).on('mousemove', zis.mouse_move_listener);
    $(document).on('click', zis.mouse_click_listener_notifier);

}
