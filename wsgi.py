from VPNcon import app

if __name__ == "__main__":
    try:
        f = open('appconf.txt')
    except IOError as e:
        print('appconf.txt not exist, creating...')
        with open("appconf.txt", "w") as f:
            f.writelines("PUT API PASSWORD INSTEAD THIS MESSAGE\n")
            f.write("PUT API WORKDIR LIKE: /your/work/dir/ INSTEAD THIS MESSAGE\n")
            f.write("PUT API IPADDRESS INSTEAD THIS MESSAGE\n")
            f.write("PUT YOUR ANSWER TO: TESTMODE?(YES/NO) INSTEAD THIS MESSAGE\n")
    else:
        auth = f.readline().strip()
        workDir = f.readline().strip()
        ipAddress = f.readline().strip()
        testMode = True if f.readline().strip() == "YES" else False
        f.close()
        app.run(debug=testMode)